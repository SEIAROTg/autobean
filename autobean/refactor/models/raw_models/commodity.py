from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .currency import Currency
from .date import Date

_Self = TypeVar('_Self', bound='Commodity')


@internal.token_model
class CommodityLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'COMMODITY'
    DEFAULT = 'commodity'


@internal.tree_model
class Commodity(base.RawTreeModel):
    RULE = 'commodity'

    @final
    def __init__(self, token_store: base.TokenStore, date: Date, label: CommodityLabel, currency: Currency):
        super().__init__(token_store)
        self.raw_date = date
        self._label = label
        self.raw_currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_currency

    @internal.required_node_property
    def raw_date(self) -> Date:
        pass

    @internal.required_node_property
    def _label(self) -> CommodityLabel:
        pass

    @internal.required_node_property
    def raw_currency(self) -> Currency:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_date),
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_date.reset(self, token_transformer.transform(self.raw_date))
        type(self)._label.reset(self, token_transformer.transform(self._label))
        type(self).raw_currency.reset(self, token_transformer.transform(self.raw_currency))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Commodity)
            and self.raw_currency == other.raw_currency)

    @classmethod
    def from_children(cls: Type[_Self], date: Date, currency: Currency) -> _Self:
        label = CommodityLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *currency.detach(),
        ])
        return cls(token_store, date, label, currency)
