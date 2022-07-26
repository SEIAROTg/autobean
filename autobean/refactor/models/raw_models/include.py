from typing import Type, TypeVar, final

from autobean.refactor.models.raw_models import punctuation
from . import base
from . import escaped_string
from . import internal

_Self = TypeVar('_Self', bound='Include')


@internal.token_model
class IncludeLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'INCLUDE'
    DEFAULT = 'include'


@internal.tree_model
class Include(base.RawTreeModel):
    RULE = 'include'

    @final
    def __init__(self, token_store: base.TokenStore, label: IncludeLabel, filename: escaped_string.EscapedString):
        super().__init__(token_store)
        self._label = label
        self._filename = filename

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._filename

    _label = internal.field[IncludeLabel]()
    _filename = internal.field[escaped_string.EscapedString]()

    raw_filename = internal.required_node_property(_filename)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self._filename))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        self._filename = token_transformer.transform(self._filename)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Include)
            and self._label == other._label
            and self._filename == other._filename)

    @classmethod
    def from_children(cls: Type[_Self], filename: escaped_string.EscapedString) -> _Self:
        label = IncludeLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            label,
            punctuation.Whitespace.from_default(),
            *filename.detach(),
        ])
        return cls(token_store, label, filename)
