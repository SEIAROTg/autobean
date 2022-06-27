from autobean.refactor import token_store as token_store_lib
from . import base
from . import escaped_string


@base.token_model
class IncludeLabel(base.RawTokenModel):
    RULE = 'INCLUDE'


@base.tree_model
class Include(base.RawTreeModel):
    RULE = 'include'

    def __init__(self, token_store: token_store_lib.TokenStore, label: IncludeLabel, filename: escaped_string.EscapedString):
        super().__init__(token_store)
        self._label = label
        self._filename = filename

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self._filename

    @property
    def raw_filename(self) -> escaped_string.EscapedString:
        return self._filename

    @raw_filename.setter
    def raw_filename(self, filename: escaped_string.EscapedString) -> None:
        self._token_store.replace(self._filename, filename)
        self._filename = filename
