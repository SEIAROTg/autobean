import datetime
from typing import Type, TypeVar
from . import internal
from .currency import Currency
from .date import Date
from .generated import commodity
from .generated.commodity import CommodityLabel

_Self = TypeVar('_Self', bound='Commodity')


@internal.tree_model
class Commodity(commodity.Commodity):

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, currency: str) -> _Self:
        return cls.from_children(Date.from_value(date), Currency.from_value(currency))
