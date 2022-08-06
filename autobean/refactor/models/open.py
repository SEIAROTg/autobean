import datetime
from typing import Iterable, Optional, Type, TypeVar

from . import internal
from .generated import open
from .generated.open import OpenLabel
from .currency import Currency
from .escaped_string import EscapedString
from .date import Date
from .account import Account

_Self = TypeVar('_Self', bound='Open')


@internal.tree_model
class Open(open.Open):
    date = internal.required_date_property(open.Open.raw_date)
    account = internal.required_string_property(open.Open.raw_account)
    currencies = internal.repeated_string_property(open.Open.raw_currencies, Currency)
    booking = internal.optional_string_property(open.Open.raw_booking, EscapedString)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            currencies: Iterable[str],
            booking: Optional[str],
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            map(Currency.from_value, currencies),
            EscapedString.from_value(booking) if booking is not None else None,
        )
