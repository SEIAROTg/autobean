# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

from typing import Optional, Type, TypeVar, final
from .. import base
from .. import internal
from ..meta_key import MetaKey
from ..meta_value import MetaRawValue
from ..punctuation import Indent, Whitespace

_Self = TypeVar('_Self', bound='MetaItem')


@internal.tree_model
class MetaItem(base.RawTreeModel):
    RULE = 'meta_item'

    _indent = internal.required_field[Indent]()
    _key = internal.required_field[MetaKey]()
    _value = internal.optional_field[MetaRawValue](separators=(Whitespace.from_default(),))

    raw_indent = internal.required_node_property(_indent)
    raw_key = internal.required_node_property(_key)
    raw_value = internal.optional_node_property(_value)

    indent = internal.required_string_property(raw_indent)
    key = internal.required_string_property(raw_key)

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            indent: Indent,
            key: MetaKey,
            value: internal.Maybe[MetaRawValue],
    ):
        super().__init__(token_store)
        self._indent = indent
        self._key = key
        self._value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._indent.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._value.last_token

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self._indent.clone(token_store, token_transformer),
            self._key.clone(token_store, token_transformer),
            self._value.clone(token_store, token_transformer),
        )
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._indent = self._indent.reattach(token_store, token_transformer)
        self._key = self._key.reattach(token_store, token_transformer)
        self._value = self._value.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, MetaItem)
            and self._indent == other._indent
            and self._key == other._key
            and self._value == other._value
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
            indent: Indent,
            key: MetaKey,
            value: Optional[MetaRawValue],
    ) -> _Self:
        maybe_value = internal.MaybeL[MetaRawValue].from_children(value, separators=cls._value.separators)
        tokens = [
            *indent.detach(),
            *key.detach(),
            *maybe_value.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        indent.reattach(token_store)
        key.reattach(token_store)
        maybe_value.reattach(token_store)
        return cls(token_store, indent, key, maybe_value)
