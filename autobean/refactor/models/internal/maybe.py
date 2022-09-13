import abc
import copy
from typing import Generic, Optional, Type, TypeVar
from .. import base
from .placeholder import Placeholder


_M = TypeVar('_M', bound=base.RawModel)
_SelfMaybe = TypeVar('_SelfMaybe', bound='Maybe')
_SelfMaybeL = TypeVar('_SelfMaybeL', bound='MaybeL')
_SelfMaybeR = TypeVar('_SelfMaybeR', bound='MaybeR')


class Maybe(base.RawTreeModel, Generic[_M]):
    def __init__(
            self,
            token_store: base.TokenStore,
            inner: Optional[_M],
            placeholder: Placeholder,
    ) -> None:
        super().__init__(token_store)
        self.inner = inner
        self._placeholder = placeholder

    @property
    def placeholder(self) -> Placeholder:
        return self._placeholder

    def clone(self: _SelfMaybe, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfMaybe:
        return type(self)(
            token_store,
            self.inner.clone(token_store, token_transformer) if self.inner is not None else None,
            self.placeholder.clone(token_store, token_transformer))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        if self.inner is not None:
            self.inner = self.inner.reattach(token_store, token_transformer)
        self._placeholder = self._placeholder.reattach(token_store, token_transformer)

    def auto_claim_comments(self) -> None:
        if self.inner is not None:
            self.inner.auto_claim_comments()

    @abc.abstractmethod
    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...]) -> None:
        ...

    @abc.abstractmethod
    def remove_inner(self, inner: _M) -> None:
        ...


class MaybeL(Maybe[_M]):
    @property
    def first_token(self) -> base.RawTokenModel:
        return self.placeholder

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.inner.last_token if self.inner is not None else self.placeholder

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, MaybeL) and self.inner == other.inner

    @classmethod
    def from_children(
            cls: Type[_SelfMaybeL],
            inner: Optional[_M],
            *,
            separators: tuple[base.RawTokenModel, ...],
    ) -> _SelfMaybeL:
        placeholder = Placeholder.from_default()
        tokens = (
            [placeholder, *copy.deepcopy(separators), *inner.detach()]
            if inner is not None else [placeholder])
        token_store = base.TokenStore.from_tokens(tokens)
        if inner is not None:
            inner.reattach(token_store)
        return cls(token_store, inner, placeholder)

    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...],) -> None:
        self.token_store.insert_after(self.placeholder, [
            *copy.deepcopy(separators),
            *inner.detach(),
        ])
        inner.reattach(self.token_store)

    def remove_inner(self, inner: _M) -> None:
        first = self.token_store.get_next(self.placeholder)
        assert first is not None
        self.token_store.remove(first, inner.last_token)


class MaybeR(Maybe[_M]):
    @property
    def first_token(self) -> base.RawTokenModel:
        return self.inner.first_token if self.inner is not None else self.placeholder

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.placeholder

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, MaybeR) and self.inner == other.inner

    @classmethod
    def from_children(
            cls: Type[_SelfMaybeR],
            inner: Optional[_M],
            *,
            separators: tuple[base.RawTokenModel, ...],
    ) -> _SelfMaybeR:
        placeholder = Placeholder.from_default()
        tokens = (
            [*inner.detach(), *copy.deepcopy(separators), placeholder]
            if inner is not None else [placeholder])
        token_store = base.TokenStore.from_tokens(tokens)
        if inner is not None:
            inner.reattach(token_store)
        return cls(token_store, inner, placeholder)

    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...],) -> None:
        self.token_store.insert_before(self.placeholder, [
            *inner.detach(),
            *copy.deepcopy(separators),
        ])
        inner.reattach(self.token_store)

    def remove_inner(self, inner: _M) -> None:
        last = self.token_store.get_prev(self.placeholder)
        assert last is not None
        self.token_store.remove(inner.first_token, last)
