import datetime
import decimal
from typing import Callable, Type, TypeVar
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
                if isinstance(self.raw_value, NumberExpr):
                    self.raw_value.value = value
                else:
                    self.raw_value = NumberExpr.from_value(value)
            case bool():
                self._update_token(value, Bool, Bool.from_value)
            case _:
                self.raw_value = value

    def _update_token(
            self,
            value: _V,
            token_type: Type[internal.SingleValueRawTokenModel[_V]],
            token_ctor: Callable[[_V], MetaValue],
    ) -> None:
        assert token_ctor == token_type.from_value
        if isinstance(self.raw_value, token_type):
            self.raw_value.value = value
        else:
            self.raw_value = token_ctor(value)
