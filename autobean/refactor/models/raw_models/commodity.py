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
        self._date = date
        self._label = label
        self._currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._currency

    _date = internal.required_field[Date]()
    _label = internal.required_field[CommodityLabel]()
    _currency = internal.required_field[Currency]()

    raw_date = internal.required_node_property(_date)
    raw_currency = internal.required_node_property(_currency)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._currency = token_transformer.transform(self._currency)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Commodity)
            and self._currency == other._currency)

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
