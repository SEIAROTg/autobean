import datetime
from typing import Type, TypeVar
from autobean.refactor.models.raw_models import commodity
from autobean.refactor.models.raw_models.commodity import CommodityLabel
from . import internal
from .currency import Currency
from .date import Date

internal.token_model(CommodityLabel)

_Self = TypeVar('_Self', bound='Commodity')


@internal.tree_model
class Commodity(commodity.Commodity):
    date = internal.required_date_property(commodity.Commodity.raw_date)
    currency = internal.required_string_property(commodity.Commodity.raw_currency)

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, currency: str) -> _Self:
        return cls.from_children(Date.from_value(date), Currency.from_value(currency))
