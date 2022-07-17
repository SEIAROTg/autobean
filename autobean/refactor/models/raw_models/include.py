from . import base
from . import escaped_string
from . import internal


@internal.token_model
class IncludeLabel(internal.SimpleRawTokenModel):
    RULE = 'INCLUDE'


@internal.tree_model
class Include(base.RawTreeModel):
    RULE = 'include'

    def __init__(self, token_store: base.TokenStore, label: IncludeLabel, filename: escaped_string.EscapedString):
        super().__init__(token_store)
        self._label = label
        self.raw_filename = filename

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_filename

    @internal.required_node_property
    def raw_filename(self) -> escaped_string.EscapedString:
        pass
