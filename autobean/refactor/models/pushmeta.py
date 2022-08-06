import datetime
import decimal
from typing import Callable, Optional, Type, TypeVar, Union
from . import internal
from .escaped_string import EscapedString
from .number_expr import NumberExpr
from .meta_key import MetaKey
from .account import Account
from .currency import Currency
from .tag import Tag
from .null import Null
from .amount import Amount
from .date import Date
from .bool import Bool
from .generated import pushmeta
from .generated.pushmeta import PushmetaLabel, MetaRawValue

_ValueTypeSimplified = str | datetime.date | decimal.Decimal | bool
_ValueTypePreserved = Account | Currency | Tag | Null | Amount
MetaValue = Union[_ValueTypeSimplified, _ValueTypePreserved]
_V = TypeVar('_V', str, datetime.date, decimal.Decimal, bool)
_Self = TypeVar('_Self', bound='Pushmeta')


@internal.tree_model
class Pushmeta(pushmeta.Pushmeta):

    @property
    def value(self) -> Optional[MetaValue]:
        if isinstance(self.raw_value, EscapedString | Date | NumberExpr | Bool):
            return self.raw_value.value
        return self.raw_value

    @value.setter
    def value(self, value: Optional[MetaValue | MetaRawValue]) -> None:
        match value:
            case str():
                self._update_token(value, EscapedString, EscapedString.from_value)
            case datetime.date():
                self._update_token(value, Date, Date.from_value)
            case decimal.Decimal():
                self._update_token(value, NumberExpr, NumberExpr.from_value)
            case bool():
                self._update_token(value, Bool, Bool.from_value)
            case _:
                self.raw_value = value

    def _update_token(
            self,
            value: _V,
            token_type: Type[internal.RWValue[_V]],
            token_ctor: Callable[[_V], MetaRawValue],
    ) -> None:
        assert token_ctor == token_type.from_value
        if isinstance(self.raw_value, token_type):
            self.raw_value.value = value
        else:
            self.raw_value = token_ctor(value)

    @classmethod
    def from_value(cls: Type[_Self], key: str, value: Optional[MetaValue | MetaRawValue]) -> _Self:
        raw_value: Optional[MetaRawValue]
        match value:
            case str():
                raw_value = EscapedString.from_value(value)
            case datetime.date():
                raw_value = Date.from_value(value)
            case decimal.Decimal():
                raw_value = NumberExpr.from_value(value)
            case bool():
                raw_value = Bool.from_value(value)
            case _:
                raw_value = value
        return cls.from_children(MetaKey.from_value(key), raw_value)
