from typing import Optional, TypeVar, final
from . import base
from . import internal

_Self = TypeVar('_Self', bound='File')


@internal.tree_model
class File(base.RawTreeModel):
    RULE = 'file'

    @final
    def __init__(self, token_store: base.TokenStore, *directives: base.RawTreeModel):
        super().__init__(token_store)
        self._directives = list(directives)

    @property
    def first_token(self) -> Optional[base.RawTokenModel]:
        return self._token_store.get_first()

    @property
    def last_token(self) -> Optional[base.RawTokenModel]:
        return self._token_store.get_last()

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            *(directive.clone(token_store, token_transformer) for directive in self._directives))
    
    def reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        for directive in self._directives:
            directive.reattach(token_store, token_transformer)
