import decimal
from . import internal
from .generated import number_unary_expr
from .generated.number_unary_expr import UnaryOp


@internal.tree_model
class NumberUnaryExpr(number_unary_expr.NumberUnaryExpr):
    @property
    def value(self) -> decimal.Decimal:
        if self._unary_op.raw_text == '+':
            return self._operand.value
        elif self._unary_op.raw_text == '-':
            return -self._operand.value
        else:
            assert False
