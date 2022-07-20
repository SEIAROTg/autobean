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
class LeftParen(internal.SimpleRawTokenModel):
    RULE = 'LEFT_PAREN'


@internal.token_model
class RightParen(internal.SimpleRawTokenModel):
    RULE = 'RIGHT_PAREN'


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
        self.raw_unary_op = unary_op
        self.raw_operand = operand

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_unary_op

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_operand.last_token

    @internal.required_node_property
    def raw_unary_op(self) -> UnaryOp:
        pass

    @internal.required_node_property
    def raw_operand(self) -> 'NumberAtomExpr':
        pass

    @property
    def value(self) -> decimal.Decimal:
        if self.raw_unary_op.raw_text == '+':
            return self.raw_operand.value
        elif self.raw_unary_op.raw_text == '-':
            return -self.raw_operand.value
        else:
            assert False

    def clone(self: _SelfNumberUnaryExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberUnaryExpr:
        operand: NumberAtomExpr
        if isinstance(self.raw_operand, number.Number):
            operand = token_transformer.transform(self.raw_operand)
        else:
            operand = self.raw_operand.clone(token_store, token_transformer)
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_unary_op),
            operand)

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_unary_op.reset(self, token_transformer.transform(self.raw_unary_op))
        if isinstance(self.raw_operand, number.Number):
            type(self).raw_operand.reset(self, token_transformer.transform(self.raw_operand))
        else:
            self.raw_operand.reattach(token_store, token_transformer)


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
        self.raw_left_paren = left_paren
        self.raw_inner_expr = inner_expr
        self.raw_right_paren = right_paren

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_left_paren

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_right_paren

    @internal.required_node_property
    def raw_left_paren(self) -> LeftParen:
        pass

    @internal.required_node_property
    def raw_inner_expr(self) -> 'NumberAddExpr':
        pass

    @internal.required_node_property
    def raw_right_paren(self) -> RightParen:
        pass

    @property
    def value(self) -> decimal.Decimal:
        return self.raw_inner_expr.value

    def clone(self: _SelfNumberParenExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberParenExpr:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_left_paren),
            self.raw_inner_expr.clone(token_store, token_transformer),
            token_transformer.transform(self.raw_right_paren))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_left_paren.reset(self, token_transformer.transform(self.raw_left_paren))
        self.raw_inner_expr.reattach(token_store, token_transformer)
        type(self).raw_right_paren.reset(self, token_transformer.transform(self.raw_right_paren))


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
    def from_children(cls: Type[_SelfNumberMulExpr], token_store: base.TokenStore, *children: Optional[base.RawModel]) -> _SelfNumberMulExpr:
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
    def from_children(cls: Type[_SelfNumberAddExpr], token_store: base.TokenStore, *children: Optional[base.RawModel]) -> _SelfNumberAddExpr:
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


@internal.tree_model
class NumberExpr(base.RawTreeModel):
    RULE = 'number_expr'

    def __init__(
            self,
            token_store: base.TokenStore,
            number_add_expr: NumberAddExpr,
    ):
        super().__init__(token_store)
        self.raw_number_add_expr = number_add_expr

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_number_add_expr.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_number_add_expr.last_token

    @internal.required_node_property
    def raw_number_add_expr(self) -> NumberAddExpr:
        pass

    @property
    def value(self) -> decimal.Decimal:
        return self.raw_number_add_expr.value

    def clone(self: _SelfNumberExpr, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfNumberExpr:
        return type(self)(
            token_store,
            self.raw_number_add_expr.clone(token_store, token_transformer))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self.raw_number_add_expr.reattach(token_store, token_transformer)
