from typing import Optional
from autobean.refactor import token_store as token_store_lib
from . import base
from . import escaped_string
from . import internal


@base.token_model
class PluginLabel(base.RawTokenModel):
    RULE = 'PLUGIN'


@base.tree_model
class Plugin(base.RawTreeModel):
    RULE = 'plugin'

    def __init__(
            self,
            token_store: token_store_lib.TokenStore,
            label: PluginLabel,
            name: escaped_string.EscapedString,
            config: Optional[escaped_string.EscapedString],
    ):
        super().__init__(token_store)
        self._label = label
        self.raw_name = name
        self.raw_config = config

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self.raw_config or self.raw_name

    @internal.required_node_property
    def raw_name(self) -> escaped_string.EscapedString:
        pass

    @internal.optional_node_property
    def raw_config(self) -> escaped_string.EscapedString:
        pass

    @raw_config.creator
    def __raw_config_creator(self, config: escaped_string.EscapedString) -> None:
        self.token_store.insert_after(self.raw_name, [base.Whitespace(' '), config])
    
    @raw_config.remover
    def __raw_config_remover(self, current: escaped_string.EscapedString) -> None:
        internal.remove_with_left_whitespace(self.token_store, current)
