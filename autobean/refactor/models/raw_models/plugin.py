from typing import Optional, Type, TypeVar, final
from . import base
from . import editor
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
            config: Optional[escaped_string.EscapedString],
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
        return self._config or self._name

    _label = internal.required_field[PluginLabel]()
    _name = internal.required_field[escaped_string.EscapedString]()
    _config = internal.optional_field[escaped_string.EscapedString](floating=internal.Floating.LEFT)

    raw_name = internal.required_node_property(_name)
    raw_config = internal.optional_node_property(_config)

    @raw_config.creator
    def __raw_config_creator(self, config: escaped_string.EscapedString) -> None:
        self.token_store.insert_after(self._name, [punctuation.Whitespace(' '), config])
    
    @raw_config.remover
    def __raw_config_remover(self, current: escaped_string.EscapedString) -> None:
        editor.remove_towards_left(self, current)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self._name),
            token_transformer.transform(self._config),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        self._name = token_transformer.transform(self._name)
        self._config = token_transformer.transform(self._config)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Plugin)
            and self._name == other._name
            and self._config == other._config)

    @classmethod
    def from_children(cls: Type[_Self], name: escaped_string.EscapedString, config: Optional[escaped_string.EscapedString] = None) -> _Self:
        label = PluginLabel.from_default()
        tokens = [
            label,
            punctuation.Whitespace.from_default(),
            name,
        ]
        if config is not None:
            tokens.extend([
                punctuation.Whitespace.from_default(),
                config,
            ])
        token_store = base.TokenStore.from_tokens(tokens)
        return cls(token_store, label, name, config)
