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
        self.raw_date = date
        self._label = label
        self.raw_name = name
        self.raw_query_string = query_string

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_query_string

    @internal.required_node_property
    def raw_date(self) -> Date:
        pass

    @internal.required_node_property
    def _label(self) -> QueryLabel:
        pass

    @internal.required_node_property
    def raw_name(self) -> EscapedString:
        pass

    @internal.required_node_property
    def raw_query_string(self) -> EscapedString:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_date),
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_name),
            token_transformer.transform(self.raw_query_string))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_date.reset(self, token_transformer.transform(self.raw_date))
        type(self)._label.reset(self, token_transformer.transform(self._label))
        type(self).raw_name.reset(self, token_transformer.transform(self.raw_name))
        type(self).raw_query_string.reset(self, token_transformer.transform(self.raw_query_string))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Query)
            and self.raw_name == other.raw_name
            and self.raw_query_string == other.raw_query_string)

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
