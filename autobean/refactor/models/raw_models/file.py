from typing import Optional
from . import base
from . import internal


@internal.tree_model
class File(base.RawTreeModel):
    RULE = 'file'

    def __init__(self, token_store: base.TokenStore, *directives: base.RawTreeModel):
        super().__init__(token_store)
        self._directives = list(directives)

    @property
    def first_token(self) -> Optional[base.RawTokenModel]:
        return self._token_store.get_first()

    @property
    def last_token(self) -> Optional[base.RawTokenModel]:
        return self._token_store.get_last()
