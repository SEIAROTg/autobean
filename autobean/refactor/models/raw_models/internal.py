from typing import Callable, Generic, Type, TypeVar, Optional
from . import base

_T = TypeVar('_T', bound=base.RawTokenModel)
_U = TypeVar('_U', bound=base.RawTreeModel)


class required_token_property(Generic[_T, _U]):
    def __init__(self, inner: Callable[[_U], _T]):
        self._attr = '_' + inner.__name__

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> _T:
        del owner
        value = getattr(instance, self._attr)
        assert value
        return getattr(instance, self._attr)

    def __set__(self, instance: _U, value: _T) -> None:
        if hasattr(instance, self._attr):
            current = self.__get__(instance)
            instance.token_store.replace(current, value)
        setattr(instance, self._attr, value)
