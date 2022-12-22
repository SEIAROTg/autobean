import decimal
from typing import Any, Iterable, Iterator, Optional
from beancount.parser import options
from beancount.core import account_types
from beancount.core.data import Custom, Directive, Posting, Transaction
from beancount.core.amount import mul
from beancount.core import realization
from autobean.utils import plugin_lib


class Realizer:
    def __init__(self, options_map: dict[str, Any]) -> None:
        self._account_types = options.get_account_types(options_map)
        self._real_root = realization.RealAccount('')

    def realize_transaction(self, transaction: Transaction) -> None:
        for posting in transaction.postings:
            if not account_types.is_balance_sheet_account(posting.account, self._account_types):
                continue
            real_account = realization.get_or_create(self._real_root, posting.account)
            real_account.balance.add_position(posting)

    def get_split_postings(self, commodity: str, multiplier: decimal.Decimal) -> Iterator[Posting]:
        for real_account in realization.iter_children(self._real_root):
            for position in real_account.balance:
                if position.units.currency != commodity or not position.units.number:
                    continue
                new_cost = position.cost._replace(number=position.cost.number / multiplier)
                yield Posting(
                    account=real_account.account,
                    units=-position.units,
                    cost=position.cost,
                    price=None,
                    flag=None,
                    meta=None)
                yield Posting(
                    account=real_account.account,
                    units=mul(position.units, multiplier),
                    cost=new_cost,
                    price=None,
                    flag=None,
                    meta=None)


@plugin_lib.plugin('autobean.stock_split')
class Plugin(plugin_lib.BasePlugin):

    def process(self, entries: list[Directive], options: dict[str, Any], arg: Optional[str]) -> Iterable[Directive]:
        self._realizer = Realizer(options)
        return super().process(entries, options, arg)

    @plugin_lib.handle_custom('autobean.stock_split', 'exactly one multiplier and one commodity')
    def handle_stock_split(
            self,
            entry: Custom,
            multiplier: decimal.Decimal,
            commodity: plugin_lib.Currency,
    ) -> Iterator[Transaction]:
        postings = self._realizer.get_split_postings(commodity, multiplier)
        txn = Transaction(
            date=entry.date,
            flag='*',
            payee=None,
            narration=f'{commodity} split {multiplier}:1',
            tags=set(),
            links=set(),
            postings=list(postings),
            meta=entry.meta,
        )
        self._realizer.realize_transaction(txn)
        yield txn

    @plugin_lib.handle(Transaction)
    def handle_txn(self, txn: Transaction) -> Iterator[Transaction]:
        self._realizer.realize_transaction(txn)
        yield txn
