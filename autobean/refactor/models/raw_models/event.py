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
        self._date = date
        self._label = label
        self._type = type
        self._description = description

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._description

    _date = internal.required_field[Date]()
    _label = internal.required_field[EventLabel]()
    _type = internal.required_field[EscapedString]()
    _description = internal.required_field[EscapedString]()

    raw_date = internal.required_node_property(_date)
    raw_type = internal.required_node_property(_type)
    raw_description = internal.required_node_property(_description)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._type),
            token_transformer.transform(self._description))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._type = token_transformer.transform(self._type)
        self._description = token_transformer.transform(self._description)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Event)
            and self._type == other._type
            and self._description == other._description)

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
