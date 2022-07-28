# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

from typing import Type, TypeVar, final
from .. import base
from .. import internal
from ..escaped_string import EscapedString
from ..punctuation import Whitespace

_Self = TypeVar('_Self', bound='Include')


@internal.token_model
class IncludeLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'INCLUDE'
    DEFAULT = 'include'


@internal.tree_model
class Include(base.RawTreeModel):
    RULE = 'include'

    _label = internal.required_field[IncludeLabel]()
    _filename = internal.required_field[EscapedString]()

    raw_filename = internal.required_node_property(_filename)

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            label: IncludeLabel,
            filename: EscapedString,
    ):
        super().__init__(token_store)
        self._label = label
        self._filename = filename

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._filename.last_token

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self._label.clone(token_store, token_transformer),
            self._filename.clone(token_store, token_transformer),
        )
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = self._label.reattach(token_store, token_transformer)
        self._filename = self._filename.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Include)
            and self._label == other._label
            and self._filename == other._filename
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
            filename: EscapedString,
    ) -> _Self:
        label = IncludeLabel.from_default()
        tokens = [
            *label.detach(),
            Whitespace.from_default(),
            *filename.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        label.reattach(token_store)
        filename.reattach(token_store)
        return cls(token_store, label, filename)
