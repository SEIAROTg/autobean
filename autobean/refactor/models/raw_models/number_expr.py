import decimal
from typing import Optional, Type, TypeVar, cast, final
from . import base
from . import internal
from . import number
from .generated import number_expr
from .generated import number_paren_expr
from .generated import number_unary_expr
from .generated.number_paren_expr import LeftParen, RightParen
from .generated.number_unary_expr import UnaryOp

# TODO: replace with PEP 673 Self once supported
_SelfNumberMulExpr = TypeVar('_SelfNumberMulExpr', bound='NumberMulExpr')
_SelfNumberAddExpr = TypeVar('_SelfNumberAddExpr', bound='NumberAddExpr')


@internal.token_model
class AddOp(internal.SimpleRawTokenModel):
    RULE = 'ADD_OP'


@internal.token_model
class MulOp(internal.SimpleRawTokenModel):
    RULE = 'MUL_OP'


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


@internal.tree_model
class NumberParenExpr(number_paren_expr.NumberParenExpr):
    @property
    def value(self) -> decimal.Decimal:
        return self._inner_expr.value


NumberAtomExpr = number.Number | NumberParenExpr | NumberUnaryExpr


@internal.tree_model
class NumberMulExpr(base.RawTreeModel):
    RULE = 'number_mul_expr'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            operands: tuple[NumberAtomExpr, ...],
            ops: tuple[MulOp, ...],
    ):
        super().__init__(token_store)
        self._raw_operands = operands
        self._raw_ops = ops

    @classmethod
    def from_parsed_children(cls: Type[_SelfNumberMulExpr], token_store: base.TokenStore, *children: Optional[base.RawModel]) -> _SelfNumberMulExpr:
        return cls(
            token_store,
            cast(tuple[NumberAtomExpr, ...], children[::2]),
            cast(tuple[MulOp, ...], children[1::2]))

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._raw_operands[0].first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._raw_operands[-1].last_token

    @property
    def raw_operands(self) -> tuple[NumberAtomExpr, ...]:
        return self._raw_operands

    @property
    def raw_ops(self) -> tuple[MulOp, ...]:
        return self._raw_ops

    @property
    def value(self) -> decimal.Decimal:
        value = self._raw_operands[0].value
        for op, operand in zip(self._raw_ops, self._raw_operands[1:]):
            if op.raw_text == '*':
                value *= operand.value
            elif op.raw_text == '/':
                value /= operand.value
            else:
                assert False
        return value

    def clone(self: _SelfNumberMulExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberMulExpr:
        ops = tuple(op.clone(token_store, token_transformer) for op in self._raw_ops)
        operands = tuple(operand.clone(token_store, token_transformer) for operand in self._raw_operands)
        return type(self)(token_store, operands, ops)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._raw_ops = tuple(op.reattach(token_store, token_transformer) for op in self._raw_ops)
        self._raw_operands = tuple(operand.reattach(token_store, token_transformer) for operand in self._raw_operands)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, NumberMulExpr)
            and self._raw_operands == other._raw_operands
            and self._raw_ops == other._raw_ops)


@internal.tree_model
class NumberAddExpr(base.RawTreeModel):
    RULE = 'number_add_expr'

    def __init__(
            self,
            token_store: base.TokenStore,
            operands: tuple[NumberMulExpr, ...],
            ops: tuple[AddOp, ...],
    ):
        super().__init__(token_store)
        self._raw_operands = operands
        self._raw_ops = ops

    @classmethod
    def from_parsed_children(cls: Type[_SelfNumberAddExpr], token_store: base.TokenStore, *children: Optional[base.RawModel]) -> _SelfNumberAddExpr:
        return cls(
            token_store,
            cast(tuple[NumberMulExpr, ...], children[::2]),
            cast(tuple[AddOp, ...], children[1::2]))

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._raw_operands[0].first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._raw_operands[-1].last_token

    @property
    def raw_operands(self) -> tuple[NumberMulExpr, ...]:
        return self._raw_operands

    @property
    def raw_ops(self) -> tuple[AddOp, ...]:
        return self._raw_ops

    @property
    def value(self) -> decimal.Decimal:
        value = self._raw_operands[0].value
        for op, operand in zip(self._raw_ops, self._raw_operands[1:]):
            if op.raw_text == '+':
                value += operand.value
            elif op.raw_text == '-':
                value -= operand.value
            else:
                assert False
        return value

    def clone(self: _SelfNumberAddExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberAddExpr:
        ops = tuple(op.clone(token_store, token_transformer) for op in self._raw_ops)
        operands = tuple(operand.clone(token_store, token_transformer) for operand in self._raw_operands)
        return type(self)(token_store, operands, ops)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._raw_ops = tuple(op.reattach(token_store, token_transformer) for op in self._raw_ops)
        self._raw_operands = tuple(operand.reattach(token_store, token_transformer) for operand in self._raw_operands)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, NumberAddExpr)
            and self._raw_operands == other._raw_operands
            and self._raw_ops == other._raw_ops)


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
