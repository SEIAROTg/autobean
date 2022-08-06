import datetime
import decimal
from typing import Optional, Type, TypeVar
from . import internal
from .account import Account
from .currency import Currency
from .date import Date
from .number_expr import NumberExpr
from .tolerance import Tolerance
from .generated import balance
from .generated.balance import BalanceLabel

_Self = TypeVar('_Self', bound='Balance')


@internal.tree_model
class Balance(balance.Balance):

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            number: decimal.Decimal,
            tolerance: Optional[decimal.Decimal],
            currency: str,
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            NumberExpr.from_value(number),
            Tolerance.from_value(tolerance) if tolerance is not None else None,
            Currency.from_value(currency))
