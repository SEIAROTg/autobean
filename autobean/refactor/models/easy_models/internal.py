import datetime
import decimal
from typing import Generic, Optional, Type, TypeVar
from autobean.refactor.models import raw_models
from autobean.refactor.models.raw_models import internal

_TT = TypeVar('_TT', bound=Type[raw_models.RawTokenModel])
_UT = TypeVar('_UT', bound=Type[raw_models.RawTreeModel])
_SV = TypeVar('_SV', bound=internal.RWValue[str])
_DV = TypeVar('_DV', bound=internal.RWValue[decimal.Decimal])
_U = TypeVar('_U', bound=raw_models.RawTreeModel)

TOKEN_MODELS: dict[str, Type[raw_models.RawTokenModel]] = {}
TREE_MODELS: dict[str, Type[raw_models.RawTreeModel]] = {}


def token_model(cls: _TT) -> _TT:
    TOKEN_MODELS[cls.RULE] = cls
    return cls


def tree_model(cls: _UT) -> _UT:
    TREE_MODELS[cls.RULE] = cls
    return cls


class required_string_property:
    def __init__(self, inner_property: internal.required_node_property[_SV]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> str:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: str) -> None:
        self._inner_property.__get__(instance).value = value


class optional_string_property(Generic[_SV]):
    def __init__(self, inner_property: internal.optional_node_property[_SV], inner_type: Type[_SV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[str]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[str]) -> None:
        s = self._inner_type.from_value(value) if value is not None else None
        self._inner_property.__set__(instance, s)


class required_decimal_property:
    def __init__(self, inner_property: internal.required_node_property[_DV]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> decimal.Decimal:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: decimal.Decimal) -> None:
        self._inner_property.__get__(instance).value = value


class optional_decimal_property(Generic[_DV]):
    def __init__(self, inner_property: internal.optional_node_property[_DV], inner_type: Type[_DV]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[decimal.Decimal]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s is not None else None
    
    def __set__(self, instance: _U, value: Optional[decimal.Decimal]) -> None:
        s = self._inner_type.from_value(value) if value is not None else None
        self._inner_property.__set__(instance, s)


class required_date_property:
    def __init__(self, inner_property: internal.required_node_property[raw_models.Date]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> datetime.date:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: datetime.date) -> None:
        self._inner_property.__get__(instance).value = value
