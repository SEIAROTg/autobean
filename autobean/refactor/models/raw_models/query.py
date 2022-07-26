from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .date import Date
from .escaped_string import EscapedString

_Self = TypeVar('_Self', bound='Query')


@internal.token_model
class QueryLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'QUERY'
    DEFAULT = 'query'


@internal.tree_model
class Query(base.RawTreeModel):
    RULE = 'query'

    @final
    def __init__(self, token_store: base.TokenStore, date: Date, label: QueryLabel, name: EscapedString, query_string: EscapedString):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._name = name
        self._query_string = query_string

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._query_string

    _date = internal.field[Date]()
    _label = internal.field[QueryLabel]()
    _name = internal.field[EscapedString]()
    _query_string = internal.field[EscapedString]()

    raw_date = internal.required_node_property(_date)
    raw_name = internal.required_node_property(_name)
    raw_query_string = internal.required_node_property(_query_string)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._name),
            token_transformer.transform(self._query_string))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._name = token_transformer.transform(self._name)
        self._query_string = token_transformer.transform(self._query_string)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Query)
            and self._name == other._name
            and self._query_string == other._query_string)

    @classmethod
    def from_children(cls: Type[_Self], date: Date, type: EscapedString, query_string: EscapedString) -> _Self:
        label = QueryLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *type.detach(),
            punctuation.Whitespace.from_default(),
            *query_string.detach(),
        ])
        return cls(token_store, date, label, type, query_string)
