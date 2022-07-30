import datetime
import decimal
from typing import Callable, Optional, Type, TypeVar
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
from .generated.pushmeta import PushmetaLabel, MetaValue

_ValueTypeSimplified = str | datetime.date | decimal.Decimal | bool
_ValueTypePreserved = Account | Currency | Tag | Null | Amount | None
_V = TypeVar('_V', str, datetime.date, decimal.Decimal, bool)
_Self = TypeVar('_Self', bound='Pushmeta')


@internal.tree_model
class Pushmeta(pushmeta.Pushmeta):
    key = internal.required_string_property(pushmeta.Pushmeta.raw_key)

    @property
    def value(self) -> _ValueTypeSimplified | _ValueTypePreserved:
        if isinstance(self.raw_value, EscapedString | Date | NumberExpr | Bool):
            return self.raw_value.value
        return self.raw_value

    @value.setter
    def value(self, value: _ValueTypeSimplified | _ValueTypePreserved) -> None:
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
            token_ctor: Callable[[_V], MetaValue],
    ) -> None:
        assert token_ctor == token_type.from_value
        if isinstance(self.raw_value, token_type):
            self.raw_value.value = value
        else:
            self.raw_value = token_ctor(value)

    @classmethod
    def from_value(cls: Type[_Self], key: str, value: _ValueTypeSimplified | _ValueTypePreserved) -> _Self:
        value_model: Optional[MetaValue]
        match value:
            case str():
                value_model = EscapedString.from_value(value)
            case datetime.date():
                value_model = Date.from_value(value)
            case decimal.Decimal():
                value_model = NumberExpr.from_value(value)
            case bool():
                value_model = Bool.from_value(value)
            case _:
                value_model = value

        return cls.from_children(MetaKey.from_value(key), value_model)
