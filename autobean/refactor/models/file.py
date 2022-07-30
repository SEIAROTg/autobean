import itertools
from typing import Iterable, Optional, Type, TypeVar, final

from . import base
from . import internal
from . import punctuation

_Self = TypeVar('_Self', bound='File')


@internal.tree_model
class File(base.RawTreeModel):
    RULE = 'file'

    @final
    def __init__(self, token_store: base.TokenStore, *directives: base.RawTreeModel):
        super().__init__(token_store)
        self._directives = list(directives)

    # TODO: remove type ignore once switched to Maybe
    @property
    def first_token(self) -> Optional[base.RawTokenModel]:  # type: ignore[override]
        return self._token_store.get_first()

    # TODO: remove type ignore once switched to Maybe
    @property
    def last_token(self) -> Optional[base.RawTokenModel]:  # type: ignore[override]
        return self._token_store.get_last()

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            *(directive.clone(token_store, token_transformer) for directive in self._directives))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        for directive in self._directives:
            directive.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, File) and self._directives == other._directives

    @classmethod
    def from_children(cls: Type[_Self], directives: Iterable[base.RawTreeModel]) -> _Self:
        directives = list(directives)
        all_tokens: list[list[base.RawTokenModel]] = []
        for i, directive in enumerate(directives):
            if i:
                all_tokens.append([punctuation.Newline.from_raw_text('\n\n')])
            all_tokens.append(directive.detach())
        token_store = base.TokenStore.from_tokens(itertools.chain.from_iterable(all_tokens))
        for directive in directives:
            directive.reattach(token_store)
        return cls(token_store, *directives)
