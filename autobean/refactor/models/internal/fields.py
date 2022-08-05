from typing import Optional, Type, TypeVar
from .. import base
from .maybe import Maybe
from .repeated import Repeated
from .base_property import base_property

_V = TypeVar('_V')
_M = TypeVar('_M', bound=base.RawModel)


class field(base_property[_V, base.RawTreeModel]):
    def __set_name__(self, owner: Type[base.RawTreeModel], name: str) -> None:
        self._attr = name

    def _get(self, instance: base.RawTreeModel) -> _V:
        return instance.__dict__[self._attr]

    def __set__(self, instance: base.RawTreeModel, value: _V) -> None:
        instance.__dict__[self._attr] = value


class required_field(field[_M]):
    pass


class optional_field(field[Maybe[_M]]):
    def __init__(self, *, separators: tuple[base.RawTokenModel, ...]) -> None:
        super().__init__()
        self._separators = separators

    @property
    def separators(self) -> tuple[base.RawTokenModel, ...]:
        return self._separators


class repeated_field(field[Repeated[_M]]):
    def __init__(
            self,
            *,
            separators: tuple[base.RawTokenModel, ...],
            separators_before: Optional[tuple[base.RawTokenModel, ...]] = None,
    ) -> None:
        super().__init__()
        self._separators = separators
        self._separators_before = separators_before

    @property
    def separators(self) -> tuple[base.RawTokenModel, ...]:
        return self._separators

    @property
    def separators_before(self) -> Optional[tuple[base.RawTokenModel, ...]]:
        return self._separators_before
