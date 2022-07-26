from typing import Type, TypeVar, final

from autobean.refactor.models.raw_models import punctuation
from . import base
from . import escaped_string
from . import internal

_Self = TypeVar('_Self', bound='Option')


@internal.token_model
class OptionLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'OPTION'
    DEFAULT = 'option'


@internal.tree_model
class Option(base.RawTreeModel):
    RULE = 'option'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            label: OptionLabel,
            key: escaped_string.EscapedString,
            value: escaped_string.EscapedString
    ):
        super().__init__(token_store)
        self._label = label
        self._key = key
        self._value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._value

    _label = internal.field[OptionLabel]()
    _key = internal.field[escaped_string.EscapedString]()
    _value = internal.field[escaped_string.EscapedString]()

    raw_key = internal.required_node_property(_key)
    raw_value = internal.required_node_property(_value)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self._key),
            token_transformer.transform(self._value))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        self._key = token_transformer.transform(self._key)
        self._value = token_transformer.transform(self._value)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Option)
            and self._label == other._label
            and self._key == other._key
            and self._value == other._value)

    @classmethod
    def from_children(cls: Type[_Self], key: escaped_string.EscapedString, value: escaped_string.EscapedString) -> _Self:
        label = OptionLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            label,
            punctuation.Whitespace.from_default(),
            key,
            punctuation.Whitespace.from_default(),
            value,
        ])
        return cls(token_store, label, key, value)
