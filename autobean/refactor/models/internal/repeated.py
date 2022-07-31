import copy
import itertools
from typing import Generic, Iterable, Type, TypeVar
from .. import base
from .placeholder import Placeholder

_M = TypeVar('_M', bound=base.RawModel)
_Self = TypeVar('_Self', bound='Repeated')


class Repeated(base.RawTreeModel, Generic[_M]):
    def __init__(
            self,
            token_store: base.TokenStore,
            items: Iterable[_M],
            placeholder: Placeholder,
    ) -> None:
        super().__init__(token_store)
        self.items = list(items)
        self._placeholder = placeholder

    @property
    def placeholder(self) -> Placeholder:
        return self._placeholder

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._placeholder

    @property
    def last_token(self) -> base.RawTokenModel:
        if self.items:
            return self.items[-1].last_token
        return self._placeholder

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, Repeated) and self.items == other.items

    @classmethod
    def from_children(
            cls: Type[_Self],
            items: Iterable[_M],
            *,
            separators: tuple[base.RawTokenModel, ...],
    ) -> _Self:
        placeholder = Placeholder.from_default()
        items = list(items)
        tokens = [
            placeholder,
            *itertools.chain.from_iterable([
                *copy.deepcopy(separators),
                *item.detach(),
            ] for item in items),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        for item in items:
            item.reattach(token_store)
        return cls(token_store, items, placeholder)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            (item.clone(token_store, token_transformer) for item in self.items),
            self.placeholder.clone(token_store, token_transformer))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self.items = [item.reattach(token_store, token_transformer) for item in self.items]
        self._placeholder = self._placeholder.reattach(token_store, token_transformer)
