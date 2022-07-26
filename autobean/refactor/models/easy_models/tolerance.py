
import decimal
from typing import Type, TypeVar
from autobean.refactor.models.raw_models import tolerance
from autobean.refactor.models.raw_models.tolerance import Tilde
from . import internal
from .number_expr import NumberExpr

internal.token_model(Tilde)

_Self = TypeVar('_Self', bound='Tolerance')


@internal.tree_model
class Tolerance(tolerance.Tolerance):
    number = internal.required_number_expr_property(tolerance.Tolerance.raw_number)

    @classmethod
    def from_value(
            cls: Type[_Self],
            number: decimal.Decimal,
    ) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number))
