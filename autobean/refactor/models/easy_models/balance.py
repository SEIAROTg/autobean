import datetime
import decimal
from typing import Optional, Type, TypeVar
from autobean.refactor.models.raw_models import balance
from autobean.refactor.models.raw_models.balance import BalanceLabel
from . import internal
from .account import Account
from .currency import Currency
from .date import Date
from .number_expr import NumberExpr
from .tolerance import Tolerance

internal.token_model(BalanceLabel)

_Self = TypeVar('_Self', bound='Balance')


@internal.tree_model
class Balance(balance.Balance):
    date = internal.required_date_property(balance.Balance.raw_date)
    account = internal.required_string_property(balance.Balance.raw_account)
    number = internal.required_number_expr_property(balance.Balance.raw_number)

    @property
    def tolerance(self) -> Optional[decimal.Decimal]:
        if self.raw_tolerance is None:
            return None
        return self.raw_tolerance.raw_number.value

    @tolerance.setter
    def tolerance(self, value: Optional[decimal.Decimal]) -> None:
        if value is None:
            self.raw_tolerance = None
        elif self.raw_tolerance is None:
            self.raw_tolerance = Tolerance.from_value(value)
        else:
            self.raw_tolerance.raw_number.value = value

    currency = internal.required_string_property(balance.Balance.raw_currency)

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
