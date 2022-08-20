import decimal
from typing import Any, Iterator
from beancount.parser import options
from beancount.core import account_types
from beancount.core.data import Amount, Custom, Directive, Posting, Transaction
from beancount.core.amount import mul
from beancount.core import realization
from autobean.utils import error_lib


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


def plugin(entries: list[Directive], options_map: dict[str, Any]) -> tuple[list[Directive], list]:
    results = []
    logger = error_lib.ErrorLogger()
    realizer = Realizer(options_map)
    
    for entry in entries:
        if not isinstance(entry, Custom) or entry.type != 'autobean.stock_split':
            if isinstance(entry, Transaction):
                realizer.realize_transaction(entry)
            results.append(entry)
            continue
        if (
                entry.values is None
                or len(entry.values) != 1
                or entry.values[0].dtype is not Amount
                or entry.values[0].value.number is None
        ):
            logger.log_error(error_lib.InvalidDirectiveError(
                entry.meta,
                'autobean.stock-split expects exactly one number and one commodity.',
                entry))
            continue

        multiplier, commodity = entry.values[0].value
        postings = realizer.get_split_postings(commodity, multiplier)
        results.append(Transaction(
            date=entry.date,
            flag='*',
            payee=None,
            narration=f'{commodity} split {multiplier}:1',
            tags=set(),
            links=set(),
            postings=list(postings),
            meta=entry.meta,
        ))

    return results, logger.errors
