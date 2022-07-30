import datetime
import decimal
import abc
from typing import Generic, Optional, Type, TypeVar
from .properties import required_node_property, optional_node_property
from .. import base


_V = TypeVar('_V')
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
