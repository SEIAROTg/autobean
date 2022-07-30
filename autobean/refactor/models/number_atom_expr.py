from typing import Any, TypeAlias, TYPE_CHECKING
from .number import Number
if TYPE_CHECKING:
    from .number_paren_expr import NumberParenExpr
    from .number_unary_expr import NumberUnaryExpr
else:
    NumberParenExpr = Any
    NumberUnaryExpr = Any

NumberAtomExpr: TypeAlias = Number | NumberParenExpr | NumberUnaryExpr
