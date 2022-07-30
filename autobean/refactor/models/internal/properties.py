from typing import Callable, Optional, TypeVar
from .base_property import base_property
from .fields import required_field, optional_field
from .maybe import Maybe
from .. import base

_M = TypeVar('_M', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)


def _replace_node(node: _M, repl: _M) -> None:
    token_store = node.token_store  # backup because the RawTokenModel.token_store may disappear
    if not token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    token_store.splice(repl.detach(), node.first_token, node.last_token)
    if isinstance(repl, base.RawTreeModel):
        repl.reattach(token_store)


class required_node_property(base_property[_M, base.RawTreeModel]):
    def __init__(self, inner_field: required_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field

    def _get(self, instance: base.RawTreeModel) -> _M:
        return self._inner_field.__get__(instance)

    def __set__(self, instance: base.RawTreeModel, value: _M) -> None:
        assert value is not None
        current = self._inner_field.__get__(instance)
        _replace_node(current, value)
        self._inner_field.__set__(instance, value)


class optional_node_property(base_property[Optional[_M], base.RawTreeModel]):
    def __init__(self, inner_field: optional_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field
        self._fcreator: Optional[Callable[[_U, Maybe[_M], _M], None]] = None
        self._fremover: Optional[Callable[[_U, Maybe[_M], _M], None]] = None

    def _get(self, instance: _U) -> Optional[_M]:
        return self._inner_field.__get__(instance).inner

    def __set__(self, instance: _U, inner: Optional[_M]) -> None:
        maybe = self._inner_field.__get__(instance)
        if maybe.inner is None and inner is not None:
            self._fcreator(instance, maybe, inner) if self._fcreator else maybe.create_inner(inner, separators=self._inner_field.separators)
        elif maybe.inner is not None and inner is None:
            self._fremover(instance, maybe, maybe.inner) if self._fremover else maybe.remove_inner(maybe.inner)
        elif maybe.inner is not None and inner is not None:
            _replace_node(maybe.inner, inner)
        maybe.inner = inner

    def creator(self, fcreator: Callable[[_U, Maybe[_M], _M], None]) -> None:
        self._fcreator = fcreator

    def remover(self, fremover: Callable[[_U, Maybe[_M], _M], None]) -> None:
        self._fremover = fremover
