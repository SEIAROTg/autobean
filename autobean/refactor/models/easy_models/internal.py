import decimal
from typing import Generic, Optional, Type, TypeVar
from autobean.refactor.models.raw_models import base
from autobean.refactor.models.raw_models import escaped_string
from autobean.refactor.models.raw_models import internal
from autobean.refactor.models.raw_models import number_expr

_ST = TypeVar('_ST', bound=internal.SingleValueRawTokenModel[str])
_U = TypeVar('_U', bound=base.RawTreeModel)


class required_string_property(Generic[_U]):
    def __init__(self, inner_property: internal.required_node_property[_ST, _U]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> str:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: str) -> None:
        self._inner_property.__get__(instance).value = value


class optional_string_property(Generic[_U]):
    def __init__(self, inner_property: internal.optional_node_property[_ST, _U], inner_type: Type[_ST]):
        self._inner_property = inner_property
        self._inner_type = inner_type

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[str]:
        s = self._inner_property.__get__(instance, owner)
        return s.value if s else None
    
    def __set__(self, instance: _U, value: Optional[str]) -> None:
        s = None if value is None else self._inner_type.from_value(value)
        self._inner_property.__set__(instance, s)


class optional_escaped_string_property(optional_string_property):
    def __init__(self, inner_property: internal.optional_node_property[escaped_string.EscapedString, _U]):
        super().__init__(inner_property, escaped_string.EscapedString)


class required_number_expr_property(Generic[_U]):
    def __init__(self, inner_property: internal.required_node_property[number_expr.NumberExpr, _U]):
        self._inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> decimal.Decimal:
        return self._inner_property.__get__(instance, owner).value
    
    def __set__(self, instance: _U, value: decimal.Decimal) -> None:
        self._inner_property.__get__(instance).value = value
