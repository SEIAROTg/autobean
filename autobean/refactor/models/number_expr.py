import copy
import decimal
from typing import Any, Callable, Literal, NoReturn, Union, overload
from . import base
from . import internal
from . import number
from .number_add_expr import NumberAddExpr, AddOp
from .number_mul_expr import NumberMulExpr, MulOp
from .number_atom_expr import NumberAtomExpr
from .number_unary_expr import NumberUnaryExpr
from .number_paren_expr import NumberParenExpr
from .spacing import Whitespace
from .generated.number_paren_expr import LeftParen, RightParen
from .generated.number_unary_expr import UnaryOp
from .generated import number_expr

_AnyNumber = Union[int, decimal.Decimal, 'NumberExpr']
_OP_INFO = {
    '__iadd__': ('+=', False),
    '__isub__': ('-=', False),
    '__imul__': ('*=', False),
    '__itruediv__': ('/=', False),
    '__add__': ('+', False),
    '__sub__': ('-', False),
    '__mul__': ('*', False),
    '__truediv__': ('/', False),
    '__radd__': ('+', True),
    '__rsub__': ('-', True),
    '__rmul__': ('*', True),
    '__rtruediv__': ('/', True),
}


def _add_expr_from_value(value: decimal.Decimal) -> NumberAddExpr:
    number_token = number.Number.from_value(abs(value))
    token_store = base.TokenStore.from_tokens([number_token])
    atom_expr: NumberAtomExpr
    if value < 0:
        op = UnaryOp.from_raw_text('-')
        token_store.insert_before(number_token, [op])
        atom_expr = NumberUnaryExpr(token_store, op, number_token)
    else:
        atom_expr = number_token
    mul_expr = NumberMulExpr(token_store, (atom_expr,), ())
    return NumberAddExpr(token_store, (mul_expr,), ())



def _operand_type_check(
        op: Callable[['NumberExpr', 'NumberExpr'], 'NumberExpr'],
) -> Callable[['NumberExpr', object], 'NumberExpr']:
    def wrapped_op(self: 'NumberExpr', other: object) -> 'NumberExpr':
        if isinstance(other, int):
            other = NumberExpr.from_value(decimal.Decimal(other))
        elif isinstance(other, decimal.Decimal):
            other = NumberExpr.from_value(other)
        if isinstance(other, NumberExpr):
            return op(self, other)
        op_name, rev = _OP_INFO[op.__name__]
        lhs: Any
        rhs: Any
        if rev:
            lhs, rhs = other, self
        else:
            lhs, rhs = self, other
        raise TypeError(
            f'unsupported operand type(s) for {op_name}: '
            f'{type(lhs).__name__!r} and {type(rhs).__name__!r}.')
    return wrapped_op


def _wrap_paren(add_expr: NumberAddExpr) -> NumberParenExpr:
    left_paren = LeftParen.from_default()
    right_paren = RightParen.from_default()
    add_expr.token_store.insert_before(add_expr.first_token, [left_paren])
    add_expr.token_store.insert_after(add_expr.last_token, [right_paren])
    return NumberParenExpr(
        add_expr.token_store, left_paren, add_expr, right_paren)


def _as_mul_expr(expr: 'NumberExpr') -> NumberMulExpr:
    if not expr.raw_number_add_expr.raw_ops:
        return expr.raw_number_add_expr.raw_operands[0]
    paren_expr = _wrap_paren(expr.raw_number_add_expr)
    mul_expr = NumberMulExpr(expr.token_store, (paren_expr,), ())
    return mul_expr


def _as_atom_expr(expr: 'NumberExpr') -> NumberAtomExpr:
    if not expr.raw_number_add_expr.raw_ops:
        mul_expr = expr.raw_number_add_expr.raw_operands[0]
        if not mul_expr.raw_ops:
            return mul_expr.raw_operands[0]
    return _wrap_paren(expr.raw_number_add_expr)


def _unary(a: 'NumberExpr', op: Literal['+', '-']) -> NumberAddExpr:
    a = copy.deepcopy(a)
    atom_expr = _as_atom_expr(a)
    unary_op = UnaryOp.from_raw_text(op)
    a.token_store.insert_before(None, [unary_op])
    unary_expr = NumberUnaryExpr(a.token_store, unary_op, atom_expr)
    mul_expr = NumberMulExpr(a.token_store, (unary_expr,), ())
    return NumberAddExpr(a.token_store, (mul_expr,), ())


@internal.tree_model
class NumberExpr(number_expr.NumberExpr, internal.RWValue[decimal.Decimal]):
    @classmethod
    def from_value(cls, value: decimal.Decimal) -> 'NumberExpr':
        add_expr = _add_expr_from_value(value)
        return cls(add_expr.token_store, add_expr)

    @property
    def value(self) -> decimal.Decimal:
        return self._number_add_expr.value

    @value.setter
    def value(self, value: decimal.Decimal) -> None:
        self.raw_number_add_expr = _add_expr_from_value(value)

    def wrap_with_parenthesis(self) -> None:
        paren_expr = _wrap_paren(self.raw_number_add_expr)
        mul_expr = NumberMulExpr(self.token_store, (paren_expr,), ())
        add_expr = NumberAddExpr(self.token_store, (mul_expr,), ())
        self._number_add_expr = add_expr

    def _iaddsub(self: 'NumberExpr', other: 'NumberExpr', op: Literal['+', '-']) -> 'NumberExpr':
        mul_expr = _as_mul_expr(other)
        add_op = AddOp.from_raw_text(op)
        self.token_store.insert_after(self.last_token, [
            Whitespace.from_default(),
            add_op,
            Whitespace.from_default(),
            *mul_expr.detach(),
        ])
        mul_expr.reattach(self.token_store)
        add_expr = NumberAddExpr(
            self.token_store,
            self.raw_number_add_expr.raw_operands + (mul_expr,),
            self.raw_number_add_expr.raw_ops + (add_op,))
        self._number_add_expr = add_expr
        return self

    @overload
    def __iadd__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __iadd__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __iadd__(self, other: 'NumberExpr') -> 'NumberExpr':
        return self._iaddsub(other, '+')

    @overload
    def __add__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __add__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __add__(self, other: 'NumberExpr') -> 'NumberExpr':
        return copy.deepcopy(self).__iadd__(other)

    @overload
    def __radd__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __radd__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __radd__(self, other: 'NumberExpr') -> 'NumberExpr':
        return other + self

    @overload
    def __isub__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __isub__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __isub__(self, other: 'NumberExpr') -> 'NumberExpr':
        return self._iaddsub(other, '-')

    @overload
    def __sub__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __sub__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __sub__(self, other: 'NumberExpr') -> 'NumberExpr':
        return copy.deepcopy(self).__isub__(other)

    @overload
    def __rsub__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __rsub__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __rsub__(self, other: 'NumberExpr') -> 'NumberExpr':
        return other - self

    def _imuldiv(self: 'NumberExpr', other: 'NumberExpr', op: Literal['*', '/']) -> 'NumberExpr':
        self_mul_expr = _as_mul_expr(self)
        atom_expr = _as_atom_expr(other)
        mul_op = MulOp.from_raw_text(op)
        self.token_store.insert_after(self_mul_expr.last_token, [
            Whitespace.from_default(),
            mul_op,
            Whitespace.from_default(),
            *atom_expr.detach(),
        ])
        atom_expr.reattach(self.token_store)
        mul_expr = NumberMulExpr(
            self.token_store,
            self_mul_expr.raw_operands + (atom_expr,),
            self_mul_expr.raw_ops + (mul_op,))
        add_expr = NumberAddExpr(self.token_store, (mul_expr,), ())
        self._number_add_expr = add_expr
        return self

    @overload
    def __imul__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __imul__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __imul__(self, other: 'NumberExpr') -> 'NumberExpr':
        return self._imuldiv(other, '*')

    @overload
    def __mul__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __mul__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __mul__(self, other: 'NumberExpr') -> 'NumberExpr':
        return copy.deepcopy(self).__imul__(other)

    @overload
    def __rmul__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __rmul__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __rmul__(self, other: 'NumberExpr') -> 'NumberExpr':
        return other * self

    @overload
    def __itruediv__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __itruediv__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __itruediv__(self, other: 'NumberExpr') -> 'NumberExpr':
        return self._imuldiv(other, '/')

    @overload
    def __truediv__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __truediv__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __truediv__(self, other: 'NumberExpr') -> 'NumberExpr':
        return copy.deepcopy(self).__itruediv__(other)

    @overload
    def __rtruediv__(self, other: _AnyNumber) -> 'NumberExpr':  # type: ignore[misc]
        ...
    @overload
    def __rtruediv__(self, other: object) -> NoReturn:
        ...
    @_operand_type_check
    def __rtruediv__(self, other: 'NumberExpr') -> 'NumberExpr':
        return other / self

    def __pos__(self) -> 'NumberExpr':
        add_expr = _unary(self, '+')
        return type(self)(add_expr.token_store, add_expr)

    def __neg__(self) -> 'NumberExpr':
        add_expr = _unary(self, '-')
        return type(self)(add_expr.token_store, add_expr)
