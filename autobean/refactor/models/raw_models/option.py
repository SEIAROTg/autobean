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
        self.raw_key = key
        self.raw_value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_value

    @internal.required_node_property
    def raw_key(self) -> escaped_string.EscapedString:
        pass

    @internal.required_node_property
    def raw_value(self) -> escaped_string.EscapedString:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_key),
            token_transformer.transform(self.raw_value))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        type(self).raw_key.reset(self, token_transformer.transform(self.raw_key))
        type(self).raw_value.reset(self, token_transformer.transform(self.raw_value))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Option)
            and self._label == other._label
            and self.raw_key == other.raw_key
            and self.raw_value == other.raw_value)

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
