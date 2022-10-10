import datetime
import decimal
import abc
import itertools
from typing import Any, Callable, Collection, Generic, Iterable, Iterator, MutableSequence, Optional, Type, TypeGuard, TypeVar, cast, overload
from .. import base
from . import indexes, base_property, properties


_V = TypeVar('_V')
_M = TypeVar('_M', bound=base.RawModel)
_M2 = TypeVar('_M2', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)
_SV = TypeVar('_SV', bound='RWValue[str]')
_ISV = TypeVar('_ISV', bound='RWValueWithIndent[str]')
_DV = TypeVar('_DV', bound='RWValue[decimal.Decimal]')
_DateV = TypeVar('_DateV', bound='RWValue[datetime.date]')
_SelfRWValue = TypeVar('_SelfRWValue', bound='RWValue')
_SelfRWValueWithIndent = TypeVar('_SelfRWValueWithIndent', bound='RWValueWithIndent')


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


class RWValueWithIndent(RWValue[_V]):
    @property
    def indent(self) -> str:
        raise NotImplementedError()

    @indent.setter
    def indent(self, indent: str) -> None:
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def from_value(cls: Type[_SelfRWValueWithIndent], value: _V, *, indent: str = '') -> _SelfRWValueWithIndent:
        raise NotImplementedError()


class required_value_property(Generic[_V, _U]):
    def __init__(self, inner_property: base_property.base_ro_property[RWValue[_V], _U]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> _V:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: _V) -> None:
        self._inner_property.__get__(instance).value = value


class optional_string_property(Generic[_SV]):
    def __init__(self, inner_property: base_property.base_rw_property[Optional[_SV], _U], inner_type: Type[_SV]):
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


class optional_indented_string_property(Generic[_ISV]):
    def __init__(
            self,
            inner_property: base_property.base_rw_property[Optional[_ISV], _U],
            inner_type: Type[_ISV],
            indent_property: base_property.base_ro_property[_SV, base.RawTreeModel]):
        self._inner_property = inner_property
        self._inner_type = inner_type
        self._indent_property = indent_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[str]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[str]) -> None:
        current = self._inner_property.__get__(instance)
        if current is not None and value is not None:
            current.value = value
        else:
            indent = self._indent_property.__get__(instance).value
            s = self._inner_type.from_value(value, indent=indent) if value is not None else None
            self._inner_property.__set__(instance, s)


class optional_decimal_property(Generic[_U]):
    def __init__(self, inner_property: base_property.base_rw_property[Optional[_DV], _U], inner_type: Type[_DV]):
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


class optional_date_property(Generic[_U]):
    def __init__(self, inner_property: base_property.base_rw_property[Optional[_DateV], _U], inner_type: Type[_DateV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[datetime.date]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[datetime.date]) -> None:
        current = self._inner_property.__get__(instance)
        if current is not None and value is not None:
            current.value = value
        else:
            s = self._inner_type.from_value(value) if value is not None else None
            self._inner_property.__set__(instance, s)


class RepeatedValueWrapper(MutableSequence[_V], Generic[_M, _V]):
    def __init__(
            self,
            raw_wrapper: properties.RepeatedNodeWrapper[_M | Any],
            raw_type: Type[_M] | tuple[Type[_M], ...],
            from_raw_type: Callable[[_M], _V],
            to_raw_type: Callable[[_V], _M],
            update_raw: Callable[[_M, _V], bool],
    ):
        self._raw_wrapper = raw_wrapper
        self._raw_type = raw_type
        self._from_raw_type = from_raw_type
        self._to_raw_type = to_raw_type
        self._update_raw = update_raw

    @property
    def indent(self) -> Optional[str]:
        return self._raw_wrapper.indent

    def _check_type(self, v: Any) -> TypeGuard[_M]:
        return isinstance(v, self._raw_type)

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[_V]:
        return (
            self._from_raw_type(item) for item in self._raw_wrapper if self._check_type(item))

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
            values = [cast(_V, value)]
        else:
            assert isinstance(value, Iterable)
            values = list(value)
        r = indexes.range_from_index(index, len(items))
        items_to_update = items[indexes.slice_from_range(r)]
        # We don't allow assignment with distinct length here because the underlying models may not be consecutive.
        if len(items_to_update) != len(values):
            raise ValueError(f'attempt to assign sequence of size {len(values)} to extended slice of size {len(items_to_update)}')
        for item, value in zip(items_to_update, values):
            if not self._update_raw(item[1], value):
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


def _update_raw(raw_value: _SV, value: str) -> bool:
    raw_value.value = value
    return True


class repeated_string_property(properties.cached_custom_property[RepeatedValueWrapper[_SV, str], base.RawTreeModel]):
    def __init__(
            self,
            inner_property: base_property.base_ro_property[properties.RepeatedNodeWrapper[_SV | _M], base.RawTreeModel],
            inner_type: Type[_SV]):
        super().__init__(lambda instance: RepeatedValueWrapper[_SV, str](
            raw_wrapper=inner_property.__get__(instance),
            raw_type=inner_type,
            from_raw_type=lambda x: x.value,
            to_raw_type=inner_type.from_value,
            update_raw=_update_raw,
        ))


class RepeatedFilteredNodeWrapper(RepeatedValueWrapper[_M, _M]):
    def __init__(
            self,
            raw_wrapper: properties.RepeatedNodeWrapper[_M | _M2],
            type: Type[_M] | tuple[Type[_M], ...]):
        super().__init__(
            raw_wrapper=raw_wrapper,
            raw_type=type,
            from_raw_type=lambda x: x,
            to_raw_type=lambda x: x,
            update_raw=lambda _, __: False,
        )


class repeated_filtered_node_property(
        properties.cached_custom_property[RepeatedFilteredNodeWrapper[_M], base.RawTreeModel]):
    def __init__(
            self,
            inner_property: base_property.base_ro_property[properties.RepeatedNodeWrapper[_M | Any], base.RawTreeModel],
            type: Type[_M] | tuple[Type[_M], ...]):
        super().__init__(
            lambda instance: RepeatedFilteredNodeWrapper(inner_property.__get__(instance), type))
