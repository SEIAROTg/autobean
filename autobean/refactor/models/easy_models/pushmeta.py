import datetime
import decimal
from typing import Callable, Type, TypeVar
from autobean.refactor.models import raw_models
from autobean.refactor.models.raw_models import internal as raw_internal
from autobean.refactor.models.raw_models.pushmeta import PushmetaLabel, PopmetaLabel
from . import internal
from .escaped_string import EscapedString
from .number_expr import NumberExpr
from .meta_key import MetaKey
from .date import Date
from .bool import Bool

internal.token_model(PushmetaLabel)
internal.token_model(PopmetaLabel)

_ValueTypeSimplified = str | datetime.date | decimal.Decimal | bool
_ValueTypePreserved = raw_models.Account | raw_models.Currency | raw_models.Tag | raw_models.Null | raw_models.Amount | None
_V = TypeVar('_V', str, datetime.date, decimal.Decimal, bool)
_SelfPushmeta = TypeVar('_SelfPushmeta', bound='Pushmeta')
_SelfPopmeta = TypeVar('_SelfPopmeta', bound='Popmeta')


@internal.tree_model
class Pushmeta(raw_models.Pushmeta):
    key = internal.required_string_property(raw_models.Pushmeta.raw_key)

    @property
    def value(self) -> _ValueTypeSimplified | _ValueTypePreserved:
        if isinstance(self.raw_value, raw_models.EscapedString | raw_models.Date | raw_models.NumberExpr | raw_models.Bool):
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
            token_type: Type[raw_internal.SingleValueRawTokenModel[_V]],
            token_ctor: Callable[[_V], raw_models.MetaValue],
    ) -> None:
        assert token_ctor == token_type.from_value
        if isinstance(self.raw_value, token_type):
            self.raw_value.value = value
        else:
            self.raw_value = token_ctor(value)


@internal.tree_model
class Popmeta(raw_models.Popmeta):
    key = internal.required_string_property(raw_models.Popmeta.raw_key)

    @classmethod
    def from_value(cls: Type[_SelfPopmeta], key: str) -> _SelfPopmeta:
        return cls.from_children(MetaKey.from_value(key))
