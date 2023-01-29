import decimal
import textwrap
from typing import Any, Callable, Iterator, Optional, TypeVar
from beancount.parser import parser
from beancount.core.data import Balance, Custom, Directive, Transaction
import pytest
from autobean.utils import error_lib
from . import policy_lib

_T = TypeVar('_T', bound=Directive)
_U = TypeVar('_U')


def _parse_doc(type: _T) -> Callable[[Callable[..., _U]], Callable[..., _U]]:
    def decorator(func: Callable[..., _U]) -> Callable[..., _U]:
        assert func.__doc__
        directive = parser.parse_one(textwrap.dedent(func.__doc__))
        assert isinstance(directive, type)
        def wrapped(*args: Any, **kwargs: Any) -> _U:
            return func(*args, directive, **kwargs)
        return wrapped
    return decorator


@_parse_doc(Transaction)
def test_parse_weighted(txn: Transaction) -> None:
    """
    2000-01-01 *
        share-Alice: 1
        share-Bob: 1.5
    """
    policy_def = policy_lib.try_parse_policy_definition(txn.meta)
    assert policy_def
    assert isinstance(policy_def.ownership, policy_lib.WeightedOwnership)
    assert policy_def.ownership.total_weight == 2.5
    assert policy_def.ownership.weights == {
        'Alice': 1,
        'Bob': 1.5,
    }
    assert policy_def.parent is None
    assert policy_def.enforced is None
    assert policy_def.conversion is None
    assert policy_def.prorated_included is None


@_parse_doc(Transaction)
def test_parse_options_prorated(txn: Transaction) -> None:
    """
    2000-01-01 *
        share_prorated: TRUE
        Assets:Foo  100.00 USD
        Assets:Bar -100.00 USD
    """
    policy_def = policy_lib.try_parse_policy_definition(txn.meta)
    assert policy_def
    assert isinstance(policy_def.ownership, policy_lib.ProratedOwnership)


@_parse_doc(Transaction)
def test_parse_empty(txn: Transaction) -> None:
    """
    2000-01-01 *
        something: 123
        Assets:Foo  100.00 USD
        Assets:Bar -100.00 USD
    """
    policy_def = policy_lib.try_parse_policy_definition(txn.meta)
    assert policy_def is None


@_parse_doc(Transaction)
def test_parse_options_only(txn: Transaction) -> None:
    """
    2000-01-01 *
        something: 123
        share_conversion: FALSE
    """
    policy_def = policy_lib.try_parse_policy_definition(txn.meta)
    assert policy_def
    assert policy_def.ownership is None
    assert policy_def.conversion == False
    assert policy_def.prorated_included is None


@_parse_doc(Transaction)
def test_parse_bad_name(txn: Transaction) -> None:
    """
    2000-01-01 *
        share-alice: 1
    """
    with pytest.raises(error_lib.PluginException, match='capitalized.*alice'):
        policy_lib.try_parse_policy_definition(txn.meta)


@_parse_doc(Transaction)
def test_parse_options_conflicted_ownership(txn: Transaction) -> None:
    """
    2000-01-01 *
        share_prorated: TRUE
        share-Alice: 1
        share-Bob: 1
        something: 123
    """
    with pytest.raises(error_lib.PluginException, match='with share_prorated'):
        policy_lib.try_parse_policy_definition(txn.meta)


@_parse_doc(Transaction)
def test_parse_unrecognized_option(txn: Transaction) -> None:
    """
    2000-01-01 *
        share-Alice: 1
        share-Bob: 1
        share_foo: 1
    """
    with pytest.raises(error_lib.PluginException, match='Unrecognized.*foo'):
        policy_lib.try_parse_policy_definition(txn.meta)


class _TestPolicyDatabase:

    @pytest.fixture(autouse=True)
    def _setup_policy_db(self) -> Iterator[None]:
        self._policy_db = policy_lib.PolicyDatabase()
        yield None

    def _create_policy(self, id: Optional[int] = None, **options: Any) -> policy_lib.PolicyDefinition:
        ownership: Optional[policy_lib.Ownership]
        if id is not None:
            ownership = policy_lib.WeightedOwnership(weights={'Alice': decimal.Decimal(id)})
        elif options.pop('prorated', None):
            ownership = policy_lib._PRORATED
        else:
            ownership = None
        return policy_lib.PolicyDefinition(
            ownership=ownership,
            **{
                'parent': None,
                'enforced': None,
                'conversion': None,
                'prorated_included': None,
                **options,
            })


class TestAddPolicy(_TestPolicyDatabase):

    def test_add_policy_unknown_parent(self) -> None:
        policy = self._create_policy(1, parent='foo')
        with pytest.raises(error_lib.PluginException, match='unknown.*foo'):
            self._policy_db.add_policy('bar', policy)

    def test_add_balance_policy_without_ownership(self) -> None:
        policy = self._create_policy(enforced=True)
        with pytest.raises(error_lib.PluginException, match='share_enforced.*ownership'):
            self._policy_db.add_policy('foo', policy)


class TestPostingPolicyResolution(_TestPolicyDatabase):

    @_parse_doc(Transaction)
    def test_keep_going(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 1
            Assets:Account 100.00 USD
                share-Alice: 42
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(2, conversion=False))
        self._policy_db.add_policy('Assets:Account:*', self._create_policy(3, prorated_included=True))
        self._policy_db.add_policy('Assets:*', self._create_policy(4, prorated_included=False))
        self._policy_db.add_policy('default', self._create_policy(5, conversion=True))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert policy.conversion == False
        assert policy.prorated_included == True

    @_parse_doc(Transaction)
    def test_priority_posting(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 1
            Assets:Account 100.00 USD
                share-Alice: 42
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(2))
        self._policy_db.add_policy('Assets:Account:*', self._create_policy(3))
        self._policy_db.add_policy('Assets:*', self._create_policy(4))
        self._policy_db.add_policy('default', self._create_policy(5))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_priority_account(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 1
            Assets:Account 100.00 USD
                share_prorated_included: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42))
        self._policy_db.add_policy('Assets:Account:*', self._create_policy(2))
        self._policy_db.add_policy('Assets:*', self._create_policy(3))
        self._policy_db.add_policy('default', self._create_policy(4))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_priority_wildcard_account_same(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 1
            Assets:Account 100.00 USD
                share_prorated_included: FALSE
        """
        self._policy_db.add_policy('Assets:Account:*', self._create_policy(42))
        self._policy_db.add_policy('Assets:*', self._create_policy(2))
        self._policy_db.add_policy('default', self._create_policy(3))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_priority_wildcard_account_parent(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 1
            Assets:Account 100.00 USD
                share_prorated_included: FALSE
        """
        self._policy_db.add_policy('Assets:*', self._create_policy(42))
        self._policy_db.add_policy('default', self._create_policy(2))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_priority_transaction(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share-Alice: 42
            Assets:Account 100.00 USD
                share_prorated_included: FALSE
        """
        self._policy_db.add_policy('default', self._create_policy(1))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_priority_default(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_prorated_included: FALSE
        """
        self._policy_db.add_policy('default', self._create_policy(42))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_missing(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_conversion: FALSE
        """
        self._policy_db.add_policy('Liabilities:*', self._create_policy(1))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        with pytest.raises(error_lib.PluginException, match='No applicable share policy'):
            self._policy_db.get_posting_policy(txn.postings[0], policy_def)

    @_parse_doc(Transaction)
    def test_incomplete(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share_conversion: FALSE
            Assets:Account 100.00 USD
                share_conversion: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(conversion=True))
        self._policy_db.add_policy('Assets:Account:*', self._create_policy(conversion=False))
        self._policy_db.add_policy('Assets:*', self._create_policy(conversion=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        with pytest.raises(error_lib.PluginException, match='No applicable share policy'):
            self._policy_db.get_posting_policy(txn.postings[0], policy_def)

    @_parse_doc(Transaction)
    def test_balance_policy_ownership_override_rejected(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share-Bob: 1
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42, enforced=True))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        with pytest.raises(error_lib.PluginException, match='override.*share_enforced'):
            self._policy_db.get_posting_policy(txn.postings[0], policy_def)

    @_parse_doc(Transaction)
    def test_share_enforced_ephemeral_unset_rejected(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_enforced: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42, enforced=True))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        with pytest.raises(error_lib.PluginException, match='unset.*share_enforced'):
            self._policy_db.get_posting_policy(txn.postings[0], policy_def)

    @_parse_doc(Transaction)
    def test_share_enforced_unset_accepted(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_enforced: FALSE
        """
        self._policy_db.add_policy('Assets:*', self._create_policy(1, enforced=True))
        self._policy_db.add_policy('Assets:Account', self._create_policy(42, enforced=False))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42
        assert policy.enforced == False

    @_parse_doc(Transaction)
    def test_balance_policy_option_accepted(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_conversion: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(
            42, enforced=True, conversion=True))

        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert policy.conversion == False

    @_parse_doc(Transaction)
    def test_prorated(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            share_prorated: TRUE
            Assets:Account 100.00 USD
        """
        policy_def = policy_lib.try_parse_policy_definition(txn.meta)
        policy = self._policy_db.get_posting_policy(txn.postings[0], policy_def)
        assert isinstance(policy.ownership, policy_lib.ProratedOwnership)

    @_parse_doc(Transaction)
    def test_update_policy(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(1))
        self._policy_db.add_policy('Assets:Account', self._create_policy(42))

        policy = self._policy_db.get_posting_policy(txn.postings[0], None)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_move_pointer(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_policy: "foo"
        """
        self._policy_db.add_policy('aaa', self._create_policy(1))
        self._policy_db.add_policy('bbb', self._create_policy(42))
        self._policy_db.add_policy('foo', self._create_policy(parent='aaa'))
        self._policy_db.add_policy('foo', self._create_policy(parent='bbb'))

        policy = self._policy_db.get_posting_policy(txn.postings[0], None)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Transaction)
    def test_move_pointer_indirect(self, txn: Transaction) -> None:
        """
        2000-01-01 *
            Assets:Account 100.00 USD
                share_policy: "foo"
        """
        self._policy_db.add_policy('aaa', self._create_policy(1))
        self._policy_db.add_policy('bbb', self._create_policy(42))
        self._policy_db.add_policy('bar', self._create_policy(parent='aaa'))
        self._policy_db.add_policy('foo', self._create_policy(parent='bar'))
        self._policy_db.add_policy('bar', self._create_policy(parent='bbb'))

        policy = self._policy_db.get_posting_policy(txn.postings[0], None)
        assert isinstance(policy.ownership, policy_lib.WeightedOwnership)
        assert policy.ownership.weights['Alice'] == 42


class TestBalancePolicyResolution(_TestPolicyDatabase):

    @_parse_doc(Balance)
    def test_priority_explicit(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
            share-Alice: 42
            share_conversion: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(1, conversion=True))
        self._policy_db.add_policy('Assets:*', self._create_policy(conversion=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy = self._policy_db.get_balance_policy(balance)
        assert policy
        assert policy.enforced == False
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Balance)
    def test_priority_account(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(conversion=False))
        self._policy_db.add_policy('Assets:*', self._create_policy(42, conversion=True, enforced=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy = self._policy_db.get_balance_policy(balance)
        assert policy
        assert policy.enforced == True
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Balance)
    def test_priority_wildcard_account(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('Assets:*', self._create_policy(42, conversion=False, enforced=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy = self._policy_db.get_balance_policy(balance)
        assert policy
        assert policy.enforced == True
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Balance)
    def test_non_balance_policy_ignored(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42))

        policy = self._policy_db.get_balance_policy(balance)
        assert not policy

    @_parse_doc(Balance)
    def test_default_ignored(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('default', self._create_policy(42, conversion=True))

        policy = self._policy_db.get_balance_policy(balance)
        assert not policy

    @_parse_doc(Balance)
    def test_non_weighted_explicit(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
            share_prorated: TRUE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42))

        with pytest.raises(error_lib.PluginException, match='must.*weighted'):
            self._policy_db.get_balance_policy(balance)

    @_parse_doc(Balance)
    def test_non_weighted_implicit(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(prorated=True))

        policy = self._policy_db.get_balance_policy(balance)
        assert not policy

    @_parse_doc(Balance)
    def test_missing_implicit(self, balance: Balance) -> None:
        """
        2000-01-01 balance Assets:Account 100.00 USD
        """
        policy = self._policy_db.get_balance_policy(balance)
        assert not policy


class TestProportionatePolicyResolution(_TestPolicyDatabase):

    @_parse_doc(Custom)
    def test_priority_explicit(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
            share-Alice: 42
            share_conversion: FALSE
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(1, conversion=True))
        self._policy_db.add_policy('Assets:*', self._create_policy(conversion=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy = self._policy_db.get_proportionate_policy(custom, 'Assets:Account')
        assert policy
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Custom)
    def test_priority_account(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(42, conversion=False))
        self._policy_db.add_policy('Assets:*', self._create_policy(1, conversion=True))
        self._policy_db.add_policy('default', self._create_policy(conversion=True))

        policy = self._policy_db.get_proportionate_policy(custom, 'Assets:Account')
        assert policy
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Custom)
    def test_priority_wildcard_account(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
        """
        self._policy_db.add_policy('Assets:*', self._create_policy(42, conversion=False))
        self._policy_db.add_policy('default', self._create_policy(1, conversion=True))

        policy = self._policy_db.get_proportionate_policy(custom, 'Assets:Account')
        assert policy
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Custom)
    def test_priority_default(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
        """
        self._policy_db.add_policy('default', self._create_policy(42, conversion=False))

        policy = self._policy_db.get_proportionate_policy(custom, 'Assets:Account')
        assert policy
        assert policy.conversion == False
        assert policy.ownership.weights['Alice'] == 42

    @_parse_doc(Custom)
    def test_non_weighted(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
        """
        self._policy_db.add_policy('Assets:Account', self._create_policy(prorated=True))

        with pytest.raises(error_lib.PluginException, match='must.*weighted'):
            self._policy_db.get_proportionate_policy(custom, 'Assets:Account')

    @_parse_doc(Custom)
    def test_missing(self, custom: Custom) -> None:
        """
        2000-01-01 custom "autobean.share.proportionate" Assets:Account
        """
        with pytest.raises(error_lib.PluginException, match='No applicable'):
            self._policy_db.get_proportionate_policy(custom, 'Assets:Account')
