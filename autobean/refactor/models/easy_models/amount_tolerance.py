import decimal
from typing import Optional, Type, TypeVar
from autobean.refactor.models.raw_models import amount_tolerance
from autobean.refactor.models.raw_models.amount_tolerance import Tilde
from . import internal
from .number_expr import NumberExpr
from .currency import Currency

internal.token_model(Tilde)

_Self = TypeVar('_Self', bound='AmountTolerance')


@internal.tree_model
class AmountTolerance(amount_tolerance.AmountTolerance):
    number = internal.required_number_expr_property(amount_tolerance.AmountTolerance.raw_number)
    tolerance = internal.optional_number_expr_property(amount_tolerance.AmountTolerance.raw_tolerance)
    currency = internal.required_string_property(amount_tolerance.AmountTolerance.raw_currency)

    @classmethod
    def from_value(
            cls: Type[_Self],
            number: decimal.Decimal,
            tolerance: Optional[decimal.Decimal],
            currency: str,
    ) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number),
            NumberExpr.from_value(tolerance) if tolerance is not None else None,
            Currency.from_value(currency))
