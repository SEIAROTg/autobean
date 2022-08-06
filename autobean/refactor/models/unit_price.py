import decimal
from typing import Optional, Type, TypeVar
from . import internal
from .generated import unit_price
from .generated.unit_price import At
from .number_expr import NumberExpr
from .currency import Currency

_Self = TypeVar('_Self', bound='UnitPrice')


@internal.tree_model
class UnitPrice(unit_price.UnitPrice):

    number = internal.optional_decimal_property(unit_price.UnitPrice.raw_number, NumberExpr)
    currency = internal.optional_string_property(unit_price.UnitPrice.raw_currency, Currency)

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
