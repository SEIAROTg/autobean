import datetime
import decimal
from typing import Callable, Generic, Optional, Type, TypeVar
from . import internal
from .base import RawTreeModel
from .bool import Bool
from .date import Date
from .escaped_string import EscapedString
from .number_expr import NumberExpr
from .meta_value import MetaRawValue, MetaValue

_U = TypeVar('_U', bound=RawTreeModel)
_V = TypeVar('_V', str, datetime.date, decimal.Decimal, bool)


# Not inside internal.value_properties to avoid circular dependencies.
class optional_meta_value_property(Generic[_U]):
    def __init__(self, inner_property: internal.base_property[Optional[MetaRawValue], _U]):
        self.inner_property = inner_property

    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> Optional[MetaValue]:
        raw_value = self.inner_property.__get__(instance, owner)
        if isinstance(raw_value, EscapedString | Date | NumberExpr | Bool):
            return raw_value.value
        return raw_value

    def __set__(self, instance: _U, value: Optional[MetaValue | MetaRawValue]) -> None:
        current_raw = self.inner_property.__get__(instance, None)
        match value:
            case str():
                self._update(instance, current_raw, value, EscapedString, EscapedString.from_value)
            case datetime.date():
                self._update(instance, current_raw, value, Date, Date.from_value)
            case decimal.Decimal():
                self._update(instance, current_raw, value, NumberExpr, NumberExpr.from_value)
            case bool():
                self._update(instance, current_raw, value, Bool, Bool.from_value)
            case _:
                self.inner_property.__set__(instance, value)

    def _update(
            self,
            instance: _U,
            current_raw: Optional[MetaRawValue],
            value: _V,
            model_type: Type[internal.RWValue[_V]],
            model_ctor: Callable[[_V], MetaRawValue],
    ) -> None:
        assert model_ctor == model_type.from_value
        if isinstance(current_raw, model_type):
            current_raw.value = value
        else:
            self.inner_property.__set__(instance, model_ctor(value))


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
