from typing import Optional, Type, TypeVar, final
from . import base
from . import punctuation
from . import escaped_string
from . import internal

_Self = TypeVar('_Self', bound='Plugin')


@internal.token_model
class PluginLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'PLUGIN'
    DEFAULT = 'plugin'


@internal.tree_model
class Plugin(base.RawTreeModel):
    RULE = 'plugin'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            label: PluginLabel,
            name: escaped_string.EscapedString,
            config: internal.Maybe[escaped_string.EscapedString],
    ):
        super().__init__(token_store)
        self._label = label
        self._name = name
        self._config = config

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._config.last_token

    _label = internal.required_field[PluginLabel]()
    _name = internal.required_field[escaped_string.EscapedString]()
    _config = internal.optional_field[escaped_string.EscapedString](floating=internal.Floating.LEFT, separators=(punctuation.Whitespace.from_default(),))

    raw_name = internal.required_node_property(_name)
    raw_config = internal.optional_node_property(_config)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self._label.clone(token_store, token_transformer),
            self._name.clone(token_store, token_transformer),
            self._config.clone(token_store, token_transformer),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = self._label.reattach(token_store, token_transformer)
        self._name = self._name.reattach(token_store, token_transformer)
        self._config = self._config.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Plugin)
            and self._name == other._name
            and self._config == other._config)

    @classmethod
    def from_children(cls: Type[_Self], name: escaped_string.EscapedString, config: Optional[escaped_string.EscapedString] = None) -> _Self:
        label = PluginLabel.from_default()
        maybe_config = internal.MaybeL.from_children(config, separators=cls._config.separators)
        tokens = [
            label,
            punctuation.Whitespace.from_default(),
            name,
            *maybe_config.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        maybe_config.reattach(token_store)
        return cls(token_store, label, name, maybe_config)
