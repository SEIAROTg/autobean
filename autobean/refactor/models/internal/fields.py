import abc
from typing import Iterable, Optional, Type, TypeVar
from .. import base
from .maybe import Maybe, MaybeL, MaybeR
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

    @abc.abstractmethod
    def create_maybe(self, value: Optional[_M]) -> Maybe[_M]:
        ...


class optional_left_field(optional_field[_M]):
    def create_maybe(self, value: Optional[_M]) -> MaybeL[_M]:
        return MaybeL.from_children(value, separators=self.separators)


class optional_right_field(optional_field[_M]):
    def create_maybe(self, value: Optional[_M]) -> MaybeR[_M]:
        return MaybeR.from_children(value, separators=self.separators)


class repeated_field(field[Repeated[_M]]):
    def __init__(
            self,
            *,
            separators: tuple[base.RawTokenModel, ...],
            separators_before: Optional[tuple[base.RawTokenModel, ...]] = None,
            default_indent: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._separators = separators
        self._separators_before = separators_before
        self._default_indent = default_indent

    @property
    def separators(self) -> tuple[base.RawTokenModel, ...]:
        return self._separators

    @property
    def separators_before(self) -> Optional[tuple[base.RawTokenModel, ...]]:
        return self._separators_before

    @property
    def default_indent(self) -> Optional[str]:
        return self._default_indent

    def create_repeated(self, values: Iterable[_M]) -> Repeated[_M]:
        return Repeated.from_children(
            values,
            separators=self.separators,
            separators_before=self.separators_before,
            indent=self.default_indent)
