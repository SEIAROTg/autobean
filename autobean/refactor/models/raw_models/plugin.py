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
        self.raw_name = name
        self.raw_config = config

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_config or self.raw_name

    @internal.required_node_property
    def _label(self) -> PluginLabel:
        pass

    @internal.required_node_property
    def raw_name(self) -> escaped_string.EscapedString:
        pass

    @internal.optional_node_property(floating=internal.Floating.LEFT)
    def raw_config(self) -> escaped_string.EscapedString:
        pass

    @raw_config.creator
    def __raw_config_creator(self, config: escaped_string.EscapedString) -> None:
        self.token_store.insert_after(self.raw_name, [punctuation.Whitespace(' '), config])
    
    @raw_config.remover
    def __raw_config_remover(self, current: escaped_string.EscapedString) -> None:
        editor.remove_towards_left(self, current)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_name),
            token_transformer.transform(self.raw_config),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self)._label.reset(self, token_transformer.transform(self._label))
        type(self).raw_name.reset(self, token_transformer.transform(self.raw_name))
        type(self).raw_config.reset(self, token_transformer.transform(self.raw_config))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Plugin)
            and self.raw_name == other.raw_name
            and self.raw_config == other.raw_config)

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
