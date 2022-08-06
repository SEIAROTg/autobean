import decimal
from typing import Type, TypeVar
from . import internal
from .number_expr import NumberExpr
from .currency import Currency
from .generated import amount

_Self = TypeVar('_Self', bound='Amount')


@internal.tree_model
class Amount(amount.Amount):

    @classmethod
    def from_value(cls: Type[_Self], number: decimal.Decimal, currency: str) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number),
            Currency.from_value(currency))
