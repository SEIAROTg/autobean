from typing import TypeVar, final
from . import base
from . import escaped_string
from . import internal

_Self = TypeVar('_Self', bound='Include')


@internal.token_model
class IncludeLabel(internal.SimpleRawTokenModel):
    RULE = 'INCLUDE'


@internal.tree_model
class Include(base.RawTreeModel):
    RULE = 'include'

    @final
    def __init__(self, token_store: base.TokenStore, label: IncludeLabel, filename: escaped_string.EscapedString):
        super().__init__(token_store)
        self._label = label
        self.raw_filename = filename

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_filename

    @internal.required_node_property
    def raw_filename(self) -> escaped_string.EscapedString:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_filename))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        type(self).raw_filename.reset(self, token_transformer.transform(self.raw_filename))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Include)
            and self._label == other._label
            and self.raw_filename == other.raw_filename)
