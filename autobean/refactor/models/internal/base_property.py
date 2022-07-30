import abc
from typing import Generic, Optional, Type, TypeVar, overload
from .. import base

_U = TypeVar('_U', bound=base.RawTreeModel)
_V = TypeVar('_V')
_Self = TypeVar('_Self', bound='base_property')


class base_property(Generic[_V, _U], abc.ABC):
    @abc.abstractmethod
    def _get(self, instance: _U) -> _V:
        ...

    @overload
    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> _V:
        ...

    @overload
    def __get__(self: _Self, instance: None, owner: Type[_U]) -> _Self:
        ...

    def __get__(self: _Self, instance: Optional[_U], owner: Optional[Type[_U]] = None) -> _V | _Self:
        del owner
        if instance is None:
            return self
        return self._get(instance)
