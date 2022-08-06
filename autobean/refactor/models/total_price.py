import decimal
from typing import Optional, Type, TypeVar
from . import internal
from .generated import total_price
from .generated.total_price import AtAt
from .number_expr import NumberExpr
from .currency import Currency

_Self = TypeVar('_Self', bound='TotalPrice')


@internal.tree_model
class TotalPrice(total_price.TotalPrice):

    @classmethod
    def from_value(
            cls: Type[_Self],
            number: Optional[decimal.Decimal],
            currency: Optional[str],
    ) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number) if number is not None else None,
            Currency.from_value(currency) if currency is not None else None,
        )
