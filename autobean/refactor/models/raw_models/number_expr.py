import decimal
from typing import Optional, Type, TypeVar, cast, final
from . import base
from . import internal
from . import number

# TODO: replace with PEP 673 Self once supported
_SelfNumberUnaryExpr = TypeVar('_SelfNumberUnaryExpr', bound='NumberUnaryExpr')
_SelfNumberParenExpr = TypeVar('_SelfNumberParenExpr', bound='NumberParenExpr')
_SelfNumberMulExpr = TypeVar('_SelfNumberMulExpr', bound='NumberMulExpr')
_SelfNumberAddExpr = TypeVar('_SelfNumberAddExpr', bound='NumberAddExpr')
_SelfNumberExpr = TypeVar('_SelfNumberExpr', bound='NumberExpr')


@internal.token_model
class UnaryOp(internal.SimpleRawTokenModel):
    RULE = 'UNARY_OP'


@internal.token_model
class AddOp(internal.SimpleRawTokenModel):
    RULE = 'ADD_OP'


@internal.token_model
class MulOp(internal.SimpleRawTokenModel):
    RULE = 'MUL_OP'


@internal.token_model
class LeftParen(internal.SimpleDefaultRawTokenModel):
    RULE = 'LEFT_PAREN'
    DEFAULT = '('


@internal.token_model
class RightParen(internal.SimpleDefaultRawTokenModel):
    RULE = 'RIGHT_PAREN'
    DEFAULT = ')'


@internal.tree_model
class NumberUnaryExpr(base.RawTreeModel):
    RULE = 'number_unary_expr'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            unary_op: UnaryOp,
            operand: 'NumberAtomExpr',
    ):
        super().__init__(token_store)
        self._unary_op = unary_op
        self._operand = operand

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._unary_op

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._operand.last_token

    _unary_op = internal.required_field[UnaryOp]()
    _operand = internal.required_field['NumberAtomExpr']()

    raw_unary_op = internal.required_node_property(_unary_op)
    raw_operand = internal.required_node_property(_operand)

    @property
    def value(self) -> decimal.Decimal:
        if self._unary_op.raw_text == '+':
            return self._operand.value
        elif self._unary_op.raw_text == '-':
            return -self._operand.value
        else:
            assert False

    def clone(self: _SelfNumberUnaryExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberUnaryExpr:
        operand: NumberAtomExpr
        if isinstance(self._operand, number.Number):
            operand = token_transformer.transform(self._operand)
        else:
            operand = self._operand.clone(token_store, token_transformer)
        return type(self)(
            token_store,
            token_transformer.transform(self._unary_op),
            operand)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._unary_op = token_transformer.transform(self._unary_op)
        if isinstance(self._operand, number.Number):
            self._operand = token_transformer.transform(self._operand)
        else:
            self._operand.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, NumberUnaryExpr)
            and self._unary_op == other._unary_op
            and self._operand == other._operand)


@internal.tree_model
class NumberParenExpr(base.RawTreeModel):
    RULE = 'number_paren_expr'

    def __init__(
            self,
            token_store: base.TokenStore,
            left_paren: LeftParen,
            inner_expr: 'NumberAddExpr',
            right_paren: RightParen,
    ):
        super().__init__(token_store)
        self._left_paren = left_paren
        self._inner_expr = inner_expr
        self._right_paren = right_paren

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._left_paren

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._right_paren

    _left_paren = internal.required_field[LeftParen]()
    _inner_expr = internal.required_field['NumberAddExpr']()
    _right_paren = internal.required_field[RightParen]()

    raw_left_paren = internal.required_node_property(_left_paren)
    raw_inner_expr = internal.required_node_property(_inner_expr)
    raw_right_paren = internal.required_node_property(_right_paren)

    @property
    def value(self) -> decimal.Decimal:
        return self._inner_expr.value

    def clone(self: _SelfNumberParenExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberParenExpr:
        return type(self)(
            token_store,
            token_transformer.transform(self._left_paren),
            self._inner_expr.clone(token_store, token_transformer),
            token_transformer.transform(self._right_paren))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._left_paren = token_transformer.transform(self._left_paren)
        self._inner_expr.reattach(token_store, token_transformer)
        self._right_paren = token_transformer.transform(self._right_paren)

    def _eq(self, other: object) -> bool:
        return (
            isinstance(other, NumberParenExpr)
            and self._left_paren == other._left_paren
            and self._inner_expr == other._inner_expr
            and self._right_paren == other._right_paren)


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
        ops = tuple(token_transformer.transform(op) for op in self._raw_ops)
        operands: list[NumberAtomExpr] = []
        for operand in self._raw_operands:
            if isinstance(operand, number.Number):
                operands.append(token_transformer.transform(operand))
            else:
                operands.append(operand.clone(token_store, token_transformer))
        return type(self)(token_store, tuple(operands), ops)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._raw_ops = tuple(map(token_transformer.transform, self._raw_ops))
        operands: list[NumberAtomExpr] = []
        for operand in self._raw_operands:
            if isinstance(operand, number.Number):
                operands.append(token_transformer.transform(operand))
            else:
                operand.reattach(token_store, token_transformer)
                operands.append(operand)
        self._raw_operands = tuple(operands)

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
        ops = tuple(token_transformer.transform(op) for op in self._raw_ops)
        operands = tuple(operand.clone(token_store, token_transformer) for operand in self._raw_operands)
        return type(self)(token_store, operands, ops)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._raw_ops = tuple(map(token_transformer.transform, self._raw_ops))
        for operand in self._raw_operands:
            operand.reattach(token_store, token_transformer)

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
class NumberExpr(base.RawTreeModel):
    RULE = 'number_expr'

    def __init__(
            self,
            token_store: base.TokenStore,
            number_add_expr: NumberAddExpr,
    ):
        super().__init__(token_store)
        self._number_add_expr = number_add_expr

    @classmethod
    def from_value(cls, value: decimal.Decimal) -> 'NumberExpr':
        add_expr = _add_expr_from_value(value)
        return cls(add_expr.token_store, add_expr)

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._number_add_expr.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._number_add_expr.last_token

    _number_add_expr = internal.required_field[NumberAddExpr]()

    raw_number_add_expr = internal.required_node_property(_number_add_expr)

    @property
    def value(self) -> decimal.Decimal:
        return self._number_add_expr.value

    @value.setter
    def value(self, value: decimal.Decimal) -> None:
        self.raw_number_add_expr = _add_expr_from_value(value)

    def clone(self: _SelfNumberExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberExpr:
        return type(self)(
            token_store,
            self._number_add_expr.clone(token_store, token_transformer))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._number_add_expr.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, NumberExpr)
            and self._number_add_expr == other._number_add_expr)
