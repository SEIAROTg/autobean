import dataclasses
import decimal
import functools
from typing import Any, Generic, Optional, TypeVar
from beancount.core import account as beancount_account
from beancount.core.data import Balance, Custom, Posting
from autobean.utils import error_lib

_T = TypeVar('_T')
_U = TypeVar('_U')
_O = TypeVar('_O', bound='Ownership')


class _SpecialMeta:
    POLICY = 'share_policy'
    ENFORCED = 'share_enforced'
    CONVERSION = 'share_conversion'
    PRORATED = 'share_prorated'
    PRORATED_INCLUDED = 'share_prorated_included'
    ALL = frozenset([POLICY, ENFORCED, CONVERSION, PRORATED, PRORATED_INCLUDED])


class Ownership:
    pass


@dataclasses.dataclass(frozen=True)
class WeightedOwnership(Ownership):
    weights: dict[str, decimal.Decimal]

    @functools.cached_property
    def total_weight(self) -> decimal.Decimal:
        return sum(self.weights.values(), decimal.Decimal(0))


class ProratedOwnership(Ownership):
    pass


_PRORATED = ProratedOwnership()


@dataclasses.dataclass(frozen=True)
class Policy(Generic[_O]):
    ownership: _O
    enforced: bool
    conversion: bool
    prorated_included: bool


@dataclasses.dataclass(frozen=True)
class PolicyDefinition:
    parent: Optional[str]
    ownership: Optional[Ownership]
    enforced: Optional[bool]
    conversion: Optional[bool]
    prorated_included: Optional[bool]

    def as_policy(self) -> Optional[Policy]:
        if not self.ownership or self.enforced is None or self.conversion is None or self.prorated_included is None:
            return None
        return Policy(
            ownership=self.ownership,
            enforced=self.enforced,
            conversion=self.conversion,
            prorated_included=self.prorated_included,
        )


_ROOT_POLICY = PolicyDefinition(
    parent=None, ownership=None, enforced=False, conversion=True, prorated_included=True)


class PolicyLookupException(error_lib.PluginException):
    pass


def _check_type(key: str, value: Any, type_: type[_T]) -> _T:
    if not isinstance(value, type_):
        raise error_lib.PluginException(f'{key} must be a {type_.__name__}')
    return value


def _get_meta(meta: dict[str, Any], key: str, type_: type[_T], default: _U) -> _T | _U:
    value = meta.get(key)
    if value is None:
        return default
    return _check_type(key, value, type_)


def try_parse_policy_definition(meta: Optional[dict[str, Any]]) -> Optional[PolicyDefinition]:
    if not meta:
        return None
    weights = {}
    for key, value in meta.items():
        if key.startswith('share-'):
            name = key.removeprefix('share-')
            if not name or not name[0].isupper():
                raise error_lib.PluginException(
                    f'Name of share parties must be capitalized: got {name!r}')
            weights[name] = _check_type(key, value, decimal.Decimal)
        elif key.startswith('share_'):
            if key not in _SpecialMeta.ALL:
                raise error_lib.PluginException(
                    f'Unrecognized share_* metadata {key!r}')
    ownership: Optional[Ownership]
    if _get_meta(meta, _SpecialMeta.PRORATED, bool, None):
        if weights:
            raise error_lib.PluginException(
                f'Cannot use share-* metadata with share_prorated')
        ownership = _PRORATED
    elif weights:
        ownership = WeightedOwnership(weights)
    else:
        ownership = None

    parent = _get_meta(meta, _SpecialMeta.POLICY, str, None)
    balance = _get_meta(meta, _SpecialMeta.ENFORCED, bool, None)
    conversion = _get_meta(meta, _SpecialMeta.CONVERSION, bool, None)
    prorate_included = _get_meta(
        meta, _SpecialMeta.PRORATED_INCLUDED, bool, None)
    if not ownership and parent is None and balance is None and conversion is None and prorate_included is None:
        return None
    return PolicyDefinition(
        parent=parent,
        ownership=ownership,
        enforced=balance,
        conversion=conversion,
        prorated_included=prorate_included,
    )


def strip_share_meta(meta: Optional[dict[str, Any]]) -> None:
    if not meta:
        return
    for key in list(meta):
        if key.startswith('share-') or key.startswith('share_'):
            del meta[key]


class PolicyDatabase:
    _named_policies: dict[str, PolicyDefinition]
    _account_policies: dict[str, PolicyDefinition]
    _wildcard_account_policies: dict[str, PolicyDefinition]

    def __init__(self) -> None:
        self._named_policies = {}
        self._account_policies = {}
        self._wildcard_account_policies = {}

    def add_policy(self, name: str, policy_def: PolicyDefinition) -> None:
        if policy_def.parent and policy_def.parent not in self._named_policies:
            raise error_lib.PluginException(
                f'Reference to unknown share policy {policy_def.parent!r}')
        if policy_def.enforced and not policy_def.ownership:
            raise error_lib.PluginException(
                f'Policy with share_enforced must define ownership')
        if name.endswith(':*'):
            self._wildcard_account_policies[name.removesuffix(':*')] = policy_def
        elif ':' in name:
            self._account_policies[name] = policy_def
        else:
            self._named_policies[name] = policy_def

    def _get_account_policy_definition(self, account: str) -> Optional[PolicyDefinition]:
        policy_def = None
        for parent in reversed(list(beancount_account.parents(account))):
            if wildcard_policy_def := self._wildcard_account_policies.get(parent):
                policy_def = _override_policy_def(
                    self._resolve_parent(wildcard_policy_def), policy_def, is_ephemeral=False)
        if account_policy_def := self._account_policies.get(account):
            policy_def = _override_policy_def(
                self._resolve_parent(account_policy_def), policy_def, is_ephemeral=False)
        return policy_def

    def _resolve_parent(self, policy_def: PolicyDefinition) -> PolicyDefinition:
        # TODO: maybe add loop detection?
        while policy_def.parent:
            policy_def = _override_policy_def(
                policy_def, self._named_policies[policy_def.parent], is_ephemeral=False)
        return policy_def

    def get_posting_policy(
            self,
            posting: Posting,
            transaction_policy_def: Optional[PolicyDefinition],
    ) -> Policy:
        policy_def = _ROOT_POLICY
        if default_policy_def := self._named_policies.get('default'):
            policy_def = _override_policy_def(
                self._resolve_parent(default_policy_def), policy_def, is_ephemeral=False)
        if transaction_policy_def:
            policy_def = _override_policy_def(
                self._resolve_parent(transaction_policy_def), policy_def, is_ephemeral=True)
        if account_policy_def := self._get_account_policy_definition(posting.account):
            policy_def = _override_policy_def(
                account_policy_def, policy_def, is_ephemeral=False)
        if posting_policy := try_parse_policy_definition(posting.meta):
            policy_def = _override_policy_def(
                self._resolve_parent(posting_policy), policy_def, is_ephemeral=True)
        if policy := policy_def.as_policy():
            return policy
        raise error_lib.PluginException('No applicable share policy')

    def get_balance_policy(self, balance: Balance) -> Optional[Policy[WeightedOwnership]]:
        has_explicit_policy = False
        balance_policy_def = try_parse_policy_definition(balance.meta)
        if balance_policy_def:
            balance_policy_def = self._resolve_parent(balance_policy_def)
        if balance_policy_def and balance_policy_def.ownership:
            if not isinstance(balance_policy_def.ownership, WeightedOwnership):
                raise error_lib.PluginException(
                    'Share policy on balance directive must have weighted ownership')
            has_explicit_policy = True
        policy_def = _ROOT_POLICY
        if account_policy_def := self._get_account_policy_definition(balance.account):
            policy_def = _override_policy_def(
                account_policy_def, policy_def, is_ephemeral=False)
        if balance_policy_def:
            policy_def = _override_policy_def(
                balance_policy_def, policy_def, is_ephemeral=True)
        if isinstance(policy_def.ownership, WeightedOwnership) and (policy_def.enforced or has_explicit_policy):
            return policy_def.as_policy()
        return None

    def get_proportionate_policy(self, custom: Custom, account: str) -> Policy[WeightedOwnership]:
        policy_def = _ROOT_POLICY
        if default_policy_def := self._named_policies.get('default'):
            policy_def = _override_policy_def(
                self._resolve_parent(default_policy_def), policy_def, is_ephemeral=False)
        if account_policy_def := self._get_account_policy_definition(account):
            policy_def = _override_policy_def(
                account_policy_def, policy_def, is_ephemeral=False)
        if custom_policy_def := try_parse_policy_definition(custom.meta):
            policy_def = _override_policy_def(
                self._resolve_parent(custom_policy_def), policy_def, is_ephemeral=True)
        policy = policy_def.as_policy()
        if not policy:
            raise error_lib.PluginException('No applicable share policy')
        if not isinstance(policy.ownership, WeightedOwnership):
            raise error_lib.PluginException(
                'Share policy on autobean.share.proportionate must have weighted ownership')
        return policy


def _override_policy_def(
        policy_def: PolicyDefinition,
        parent: Optional[PolicyDefinition],
        *,
        is_ephemeral: bool,
) -> PolicyDefinition:
    if parent is None:
        return policy_def
    if is_ephemeral:
        if parent.enforced and policy_def.ownership:
            raise error_lib.PluginException(
                'Cannot temporarily override ownership of a policy with share_enforced: TRUE')
        if parent.enforced and policy_def.enforced == False:
            raise error_lib.PluginException(
                'Cannot unset share_enforced')
    ownership = policy_def.ownership or parent.ownership
    balance = policy_def.enforced if policy_def.enforced is not None else parent.enforced
    conversion = policy_def.conversion if policy_def.conversion is not None else parent.conversion
    prorate_included = policy_def.prorated_included if policy_def.prorated_included is not None else parent.prorated_included
    return PolicyDefinition(
        parent=parent.parent,
        ownership=ownership,
        enforced=balance,
        conversion=conversion,
        prorated_included=prorate_included,
    )
