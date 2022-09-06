import datetime
import decimal
from typing import Generic, Optional, Type, TypeVar, overload
from . import internal
from .base import RawTreeModel
from .bool import Bool
from .date import Date
from .escaped_string import EscapedString
from .number_expr import NumberExpr
from .meta_value import MetaRawValue, MetaValue

_U = TypeVar('_U', bound=RawTreeModel)


# Not inside internal.value_properties to avoid circular dependencies.
class optional_meta_value_property(Generic[_U]):
    def __init__(self, inner_property: internal.base_rw_property[Optional[MetaRawValue], _U]):
        self.inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[MetaValue]:
        raw_value = self.inner_property.__get__(instance, owner)
        if isinstance(raw_value, EscapedString | Date | NumberExpr | Bool):
            return raw_value.value
        return raw_value

    def __set__(self, instance: _U, value: Optional[MetaValue | MetaRawValue]) -> None:
        current_raw = self.inner_property.__get__(instance, None)
        if not update_value(current_raw, value):
            self.inner_property.__set__(instance, from_value(value))


def update_value(raw_value: Optional[MetaRawValue], value: Optional[MetaValue | MetaRawValue]) -> bool:
    match raw_value, value:
        case EscapedString() as m, str() as v:
            m.value = v
        case Date() as m, datetime.date() as v:
            m.value = v
        case NumberExpr() as m, decimal.Decimal() as v:
            m.value = v
        case Bool() as m, bool() as v:
            m.value = v
        case _:
            return False
    return True


def from_value(value: Optional[MetaValue | MetaRawValue]) -> Optional[MetaRawValue]:
    match value:
        case str():
            return EscapedString.from_value(value)
        case datetime.date():
            return Date.from_value(value)
        case decimal.Decimal():
            return NumberExpr.from_value(value)
        case bool():
            return Bool.from_value(value)
    return value
