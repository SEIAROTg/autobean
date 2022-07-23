from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .date import Date
from .escaped_string import EscapedString

_Self = TypeVar('_Self', bound='Event')


@internal.token_model
class EventLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'EVENT'
    DEFAULT = 'event'


@internal.tree_model
class Event(base.RawTreeModel):
    RULE = 'event'

    @final
    def __init__(self, token_store: base.TokenStore, date: Date, label: EventLabel, type: EscapedString, description: EscapedString):
        super().__init__(token_store)
        self.raw_date = date
        self._label = label
        self.raw_type = type
        self.raw_description = description

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_description

    @internal.required_node_property
    def raw_date(self) -> Date:
        pass

    @internal.required_node_property
    def raw_type(self) -> EscapedString:
        pass

    @internal.required_node_property
    def raw_description(self) -> EscapedString:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_date),
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_type),
            token_transformer.transform(self.raw_description))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_date.reset(self, token_transformer.transform(self.raw_date))
        self._label = token_transformer.transform(self._label)
        type(self).raw_type.reset(self, token_transformer.transform(self.raw_type))
        type(self).raw_description.reset(self, token_transformer.transform(self.raw_description))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Event)
            and self.raw_type == other.raw_type
            and self.raw_description == other.raw_description)

    @classmethod
    def from_children(cls: Type[_Self], date: Date, type: EscapedString, description: EscapedString) -> _Self:
        label = EventLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *type.detach(),
            punctuation.Whitespace.from_default(),
            *description.detach(),
        ])
        return cls(token_store, date, label, type, description)
