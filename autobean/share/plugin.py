import collections
import decimal
import re
from typing import Any, Iterable, Iterator, Optional
from beancount.core import flags, account as account_lib
from beancount.core.data import Balance, Custom, Directive, Open, Pad, Transaction, new_metadata
from beancount.core.amount import Amount
from beancount.ops import pad, validation
from autobean.utils import error_lib, plugin_lib
from . import include, include_context, policy_lib, split_account

_DEFAULT_RECEIVABLE_ACCOUNT = 'Assets:Receivables'
_SUBACCOUNT_REGEX = re.compile(r':\[.*\]$')


@plugin_lib.plugin('autobean.share', param_type=str, custom_scope=r'autobean\.share($|\..*)')
class Plugin(plugin_lib.BasePlugin):

    def process(self, entries: list[Directive], options: dict[str, Any], arg: Optional[str]) -> Iterable[Directive]:
        self._enabled = True
        self._policy_db = policy_lib.PolicyDatabase()
        self._subaccounts = collections.defaultdict[str, set[str]](set)
        self._has_deferred_pad = False
        self._opened_accounts = set[str]()
        self._opened_account_ancestors = set[str]()
        self._receivable_account = _DEFAULT_RECEIVABLE_ACCOUNT
        errors = validation.validate(entries, options)
        self._error_logger.log_errors(errors)

        assert isinstance(arg, str)
        context = include_context.IncludeContext(viewpoint=arg)
        with include_context.try_enter_context(context) as effective_context:
            # process included files and links
            entries, errors = include.IncludePlugin.plugin(entries, options)
            self._error_logger.log_errors(errors)

            self._account_splitter = split_account.AccountSplitter(
                policy_db=self._policy_db,
                options=options,
                viewpoint=effective_context.viewpoint,
                asserted_accounts=get_asserted_accounts(entries))
            self._is_top_level = effective_context is context
            entries = list(super().process(entries, options, arg))
            if self._has_deferred_pad:
                entries, errors = pad.pad(entries, options)
                self._error_logger.log_errors(errors)
            if self._is_top_level:
                entries = self._account_splitter.process_open_close(entries)
            return entries

    def _check_enabled(self, entry: Custom) -> None:
        if not self._enabled:
            raise error_lib.PluginException(
                f'Cannot use {entry.type} while autobean.share is disabled')

    def _check_account_has_opened_descendants(self, account: str) -> None:
        if account not in self._opened_account_ancestors:
            raise error_lib.PluginException(
                f'Invalid reference to unknown account {account!r}')

    def _is_enabled(self) -> bool:
        return self._enabled

    def _is_receivable_account(self, account: str) -> bool:
        return (
            account == self._receivable_account or
            account.startswith(self._receivable_account + ':'))

    def _is_generated_account(self, account: str) -> bool:
        return (
            self._is_receivable_account(account) or
            re.search(_SUBACCOUNT_REGEX, account) is not None)

    def _open_account_if_not_opened(self, account: str, directive: Directive) -> Iterator[Open]:
        if account not in self._opened_accounts:
            self._opened_accounts.add(account)
            yield Open(
                meta=new_metadata(directive.meta['filename'], directive.meta['lineno']),
                date=directive.date,
                account=account,
                currencies=None,
                booking=None)

    # configs

    @plugin_lib.handle_custom('autobean.share.enable', 'exactly one bool')
    def handle_enable(self, entry: Custom, enable: bool) -> Iterable[Directive]:
        self._enabled = enable
        return ()

    @plugin_lib.handle_custom('autobean.share.receivable-account', 'exactly one account')
    def handle_receivable_account(self, entry: Custom, account: plugin_lib.Account) -> Iterable[Directive]:
        self._check_enabled(entry)
        self._receivable_account = account
        return ()

    @plugin_lib.handle_custom('autobean.share.policy', 'exactly one name or account')
    def handle_policy_def(self, entry: Custom, name: str | plugin_lib.Account) -> Iterable[Directive]:
        self._check_enabled(entry)
        policy_def = policy_lib.try_parse_policy_definition(entry.meta)
        if not policy_def:
            raise error_lib.PluginException('Empty share policy definition')
        self._policy_db.add_policy(name, policy_def)
        return ()

    # deferred directives

    @plugin_lib.handle_custom('autobean.share.balance', 'an account and an amount')
    def handle_deferred_balance(self, entry: Custom, account: plugin_lib.Account, amount: Amount) -> Iterator[Directive]:
        return self.handle_deferred_balance_tolerance(account, amount, None)

    @plugin_lib.handle_custom('autobean.share.balance', 'an account, an amount and a tolerance')
    def handle_deferred_balance_tolerance(self, entry: Custom, account: plugin_lib.Account | str, amount: Amount, tolerance: Optional[decimal.Decimal]) -> Iterator[Directive]:
        if not self._is_top_level:
            yield entry
            return
        self._check_enabled(entry)
        if not self._is_generated_account(account):
            raise error_lib.PluginException(f'autobean.share.balance must only be used on generated accounts')
        yield Balance(
            account=account,
            amount=amount,
            tolerance=tolerance,
        )

    @plugin_lib.handle_custom('autobean.share.pad', 'an account and an source account')
    def handle_deferred_pad(self, entry: Custom, account: plugin_lib.Account | str, source_account: plugin_lib.Account | str) -> Iterator[Directive]:
        if not self._is_top_level:
            yield entry
            return
        self._check_enabled(entry)
        if not self._is_generated_account(account) or not self._is_generated_account(source_account):
            raise error_lib.PluginException(f'autobean.share.pad must only be used on generated accounts')
        self._has_deferred_pad = True
        yield Pad(
            account=account,
            source_account=source_account,
        )

    # checks

    @plugin_lib.handle(Balance, when=_is_enabled)
    def handle_balance(self, entry: Balance) -> Iterator[Directive]:
        if self._is_generated_account(entry.account):
            raise error_lib.PluginException(
                f'balance must not be used on generated accounts. Consider using autobean.share.balance instead.')
        self._check_account_has_opened_descendants(entry.account)
        yield from self._account_splitter.process_balance(entry, self._error_logger)

    @plugin_lib.handle_custom('autobean.share.proportionate', 'exactly one account')
    def handle_proportionate(self, entry: Custom, account: plugin_lib.Account) -> Iterator[Directive]:
        self._check_enabled(entry)
        if self._is_generated_account(account):
            raise error_lib.PluginException(f'autobean.share.proportionate must not be used on generated accounts')
        self._check_account_has_opened_descendants(account)
        if custom := self._account_splitter.process_proportionate(entry, account):
            yield custom

    # transformations

    @plugin_lib.handle(Transaction, when=_is_enabled)
    def handle_transaction(self, entry: Transaction) -> Iterator[Directive]:
        if transaction := self._account_splitter.process_transaction(entry, self._receivable_account):
            for posting in transaction.postings:
                if self._is_receivable_account(posting.account):
                    yield from self._open_account_if_not_opened(posting.account, transaction)
            yield transaction

    @plugin_lib.handle(Pad, when=_is_enabled)
    def handle_pad(self, entry: Pad) -> Iterator[Directive]:
        # This should be rarely visited as pad is usually evaluated before this plugin.
        if self._is_generated_account(entry.account) or self._is_generated_account(entry.source_account):
            raise error_lib.PluginException(
                f'pad must not be used on generated accounts. Consider using autobean.share.pad instead.')
        yield entry

    @plugin_lib.handle(Open)
    def handle_open(self, entry: Open) -> Iterator[Directive]:
        yield entry
        self._opened_accounts.add(entry.account)
        for parent in account_lib.parents(entry.account):
            self._opened_account_ancestors.add(parent)
        if self._is_enabled():
            policy_def = policy_lib.try_parse_policy_definition(entry.meta)
            if policy_def:
                policy_lib.strip_share_meta(entry.meta)
                self._policy_db.add_policy(entry.account, policy_def)


def get_asserted_accounts(entries: Iterable[Directive]) -> set[str]:
    accounts = set()
    for entry in entries:
        if isinstance(entry, Balance):
            accounts.add(entry.account)
        elif (
                isinstance(entry, Custom) and
                entry.type == 'autobean.share.proportionate' and
                entry.values and
                isinstance(entry.values[0].value, str)):
            accounts.add(entry.values[0].value)
    return accounts
