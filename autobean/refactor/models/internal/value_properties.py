import datetime
import decimal
import abc
import itertools
from typing import Callable, Collection, Generic, Iterable, Iterator, MutableSequence, Optional, Type, TypeVar, overload
from .properties import RepeatedNodeWrapper, repeated_node_property, required_node_property, optional_node_property
from .. import base
from . import indexes


_V = TypeVar('_V')
_M = TypeVar('_M', bound=base.RawModel)
_M2 = TypeVar('_M2', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)
_SV = TypeVar('_SV', bound='RWValue[str]')
_DV = TypeVar('_DV', bound='RWValue[decimal.Decimal]')
_DateV = TypeVar('_DateV', bound='RWValue[datetime.date]')
_SelfRWValue = TypeVar('_SelfRWValue', bound='RWValue')


class RWValue(base.RawModel, abc.ABC, Generic[_V]):
    @property
    def value(self) -> _V:
        raise NotImplementedError()

    @value.setter
    def value(self, value: _V) -> None:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def from_value(cls: Type[_SelfRWValue], value: _V) -> _SelfRWValue:
        raise NotImplementedError()


class required_string_property:
    def __init__(self, inner_property: required_node_property[_SV]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> str:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: str) -> None:
        self._inner_property.__get__(instance).value = value


class optional_string_property(Generic[_SV]):
    def __init__(self, inner_property: optional_node_property[_SV], inner_type: Type[_SV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[str]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[str]) -> None:
        current = self._inner_property.__get__(instance)
        if current is not None and value is not None:
            current.value = value
        else:
            s = self._inner_type.from_value(value) if value is not None else None
            self._inner_property.__set__(instance, s)


class required_decimal_property:
    def __init__(self, inner_property: required_node_property[_DV]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> decimal.Decimal:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: decimal.Decimal) -> None:
        self._inner_property.__get__(instance).value = value


class optional_decimal_property(Generic[_DV]):
    def __init__(self, inner_property: optional_node_property[_DV], inner_type: Type[_DV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[decimal.Decimal]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[decimal.Decimal]) -> None:
        current = self._inner_property.__get__(instance)
        if current is not None and value is not None:
            current.value = value
        else:
            s = self._inner_type.from_value(value) if value is not None else None
            self._inner_property.__set__(instance, s)


class required_date_property:
    def __init__(self, inner_property: required_node_property[_DateV]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> datetime.date:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: datetime.date) -> None:
        self._inner_property.__get__(instance).value = value


class RepeatedValueWrapper(MutableSequence[_V], Generic[_M, _V]):
    def __init__(
            self,
            raw_wrapper: RepeatedNodeWrapper[_M | _M2],
            raw_type: Type[_M],
            type: Type[_V],
            from_raw_type: Callable[[_M], _V],
            to_raw_type: Callable[[_V], _M],
            update_raw: Callable[[_M, _V], None],
    ):
        self._raw_wrapper = raw_wrapper
        self._raw_type = raw_type
        self._type = type
        self._from_raw_type = from_raw_type
        self._to_raw_type = to_raw_type
        self._update_raw = update_raw

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[_V]:
        return (
            self._from_raw_type(item) for item in self._raw_wrapper if isinstance(item, self._raw_type))

    def _filtered_items(self) -> list[tuple[int, _M]]:
        return [(i, item) for i, item in enumerate(self._raw_wrapper) if isinstance(item, self._raw_type)]

    @overload
    def __getitem__(self, index: int) -> _V:
        ...
    @overload
    def __getitem__(self, index: slice) -> list[_V]:
        ...
    def __getitem__(self, index: int | slice) -> _V | list[_V]:
        items = self._filtered_items()
        if isinstance(index, int):
            return self._from_raw_type(items[index][1])
        return [self._from_raw_type(item[1]) for item in items[index]]

    def __delitem__(self, index: int | slice) -> None:
        items = self._filtered_items()
        r = indexes.range_from_index(index, len(items))
        self._raw_wrapper.drop_many(items[i][0] for i in r)

    @overload
    def __setitem__(self, index: int, value: _V) -> None:
        ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[_V]) -> None:
        ...
    def __setitem__(self, index: int | slice, value: _V | Iterable[_V]) -> None:
        items = self._filtered_items()
        if isinstance(index, int):
            assert isinstance(value, self._type)
            values = [value]
        else:
            assert isinstance(value, Iterable)
            values = list(value)
        r = indexes.range_from_index(index, len(items))
        items_to_update = items[indexes.slice_from_range(r)]
        # We don't allow assignment with distinct length here because the underlying models may not be consecutive.
        if len(items_to_update) != len(values):
            raise ValueError(f'attempt to assign sequence of size {len(values)} to extended slice of size {len(items_to_update)}')
        for item, value in zip(items_to_update, values):
            if isinstance(item[1], self._raw_type):
                self._update_raw(item[1], value)
            else:
                self._raw_wrapper[item[0]] = self._to_raw_type(value)

    def insert(self, index: int, value: _V) -> None:
        items = self._filtered_items()
        if index >= len(items):
            underlying_index = len(self._raw_wrapper)
        elif index < -len(items):
            underlying_index = 0
        else:
            underlying_index = items[index][0]
        self._raw_wrapper.insert(underlying_index, self._to_raw_type(value))

    def append(self, value: _V) -> None:
        self._raw_wrapper.append(self._to_raw_type(value))

    def clear(self) -> None:
        items = self._filtered_items()
        self._raw_wrapper.drop_many(item[0] for item in items)

    def extend(self, values: Iterable[_V]) -> None:
        self._raw_wrapper.extend(self._to_raw_type(value) for value in values)

    def pop(self, index: int = -1) -> _V:
        items = self._filtered_items()
        if not items:
            raise IndexError('pop from empty list')
        if not -len(items) <= index < len(items):
            raise IndexError('pop index out of range')
        underlying_index = items[index][0]
        self._raw_wrapper.pop(underlying_index)
        return self._from_raw_type(items[index][1])

    def remove(self, value: _V) -> None:
        items = self._filtered_items()
        for i, item in items:
            if self._from_raw_type(item) == value:
                self._raw_wrapper.pop(i)
                return
        raise ValueError(f'{value!r} not found in list')

    def discard(self, value: _V) -> None:
        items = self._filtered_items()
        self._raw_wrapper.drop_many(item[0] for item in items if self._from_raw_type(item[1]) == value)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Collection) and
            all(a == b for a, b in itertools.zip_longest(self, other)))


class repeated_string_property(Generic[_SV]):
    def __init__(self, inner_property: repeated_node_property[_SV | _M], inner_type: Type[_SV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __set_name__(self, owner: base.RawTreeModel, name: str) -> None:
        self._name = name

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> RepeatedValueWrapper[_SV, str]:
        inner_wrapper = self._inner_property.__get__(instance, owner)
        def update_raw(raw_value: _SV, value: str) -> None:
            raw_value.value = value

        wrapper = RepeatedValueWrapper(
            raw_wrapper=inner_wrapper,
            raw_type=self._inner_type,
            type=str,
            from_raw_type=lambda x: x.value,
            to_raw_type=self._inner_type.from_value,
            update_raw=update_raw,
        )
        setattr(instance, self._name, wrapper)
        return wrapper
