import decimal
from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .number_expr import NumberExpr

_Self = TypeVar('_Self', bound='Tolerance')


@internal.token_model
class Tilde(internal.SimpleDefaultRawTokenModel):
    RULE = 'TILDE'
    DEFAULT = '~'


@internal.tree_model
class Tolerance(base.RawTreeModel):
    RULE = 'tolerance'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            tilde: Tilde,
            number: NumberExpr,
    ):
        super().__init__(token_store)
        self._tilde = tilde
        self._number = number

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._tilde

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_number.last_token

    _tilde = internal.required_field[Tilde]()
    _number = internal.required_field[NumberExpr]()

    raw_number = internal.required_node_property(_number)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._tilde),
            self.raw_number.clone(token_store, token_transformer))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._tilde = token_transformer.transform(self._tilde)
        self._number.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Tolerance)
            and self._number == other._number)

    @classmethod
    def from_children(
            cls: Type[_Self],
            number: NumberExpr,
    ) -> _Self:
        tilde = Tilde.from_default()
        tokens = [
            *tilde.detach(),
            punctuation.Whitespace.from_default(),
            *number.detach()
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        number.reattach(token_store)
        return cls(token_store, tilde, number)
