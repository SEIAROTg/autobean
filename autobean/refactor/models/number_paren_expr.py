import decimal
from . import internal
from .generated import number_paren_expr
from .generated.number_paren_expr import LeftParen, RightParen


@internal.tree_model
class NumberParenExpr(number_paren_expr.NumberParenExpr):
    @property
    def value(self) -> decimal.Decimal:
        return self._inner_expr.value
