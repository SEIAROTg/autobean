from typing import Optional
from autobean.refactor import token_store as token_store_lib
from . import base
from . import escaped_string


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
            config: Optional[escaped_string.EscapedString]
    ):
        super().__init__(token_store)
        self._label = label
        self._name = name
        self._config = config

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self._config or self._name

    @property
    def raw_name(self) -> escaped_string.EscapedString:
        return self._name

    @raw_name.setter
    def raw_name(self, name: escaped_string.EscapedString) -> None:
        self._token_store.replace(self._name, name)
        self._name = name

    @property
    def raw_config(self) -> Optional[escaped_string.EscapedString]:
        return self._config
