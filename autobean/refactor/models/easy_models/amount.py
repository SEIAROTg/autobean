import decimal
from typing import Type, TypeVar
from autobean.refactor.models.raw_models import amount
from . import internal
from .number_expr import NumberExpr
from .currency import Currency

_Self = TypeVar('_Self', bound='Amount')


@internal.tree_model
class Amount(amount.Amount):
    number = internal.required_number_expr_property(amount.Amount.raw_number)
    currency = internal.required_string_property(amount.Amount.raw_currency)

    @classmethod
    def from_value(cls: Type[_Self], number: decimal.Decimal, currency: str) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number),
            Currency.from_value(currency))
