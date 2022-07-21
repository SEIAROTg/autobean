from typing import TypeVar, final
from . import base
from . import internal
from .currency import Currency
from .number_expr import NumberExpr

_Self = TypeVar('_Self', bound='Amount')


@internal.tree_model
class Amount(base.RawTreeModel):
    RULE = 'amount'

    @final
    def __init__(self, token_store: base.TokenStore, number_expr: NumberExpr, currency: Currency):
        super().__init__(token_store)
        self.raw_number_expr = number_expr
        self.raw_currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_number_expr.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_currency

    @internal.required_node_property
    def raw_number_expr(self) -> NumberExpr:
        pass

    @internal.required_node_property
    def raw_currency(self) -> Currency:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self.raw_number_expr.clone(token_store, token_transformer),
            token_transformer.transform(self.raw_currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self.raw_number_expr.reattach(token_store, token_transformer)
        type(self).raw_currency.reset(self, token_transformer.transform(self.raw_currency))
