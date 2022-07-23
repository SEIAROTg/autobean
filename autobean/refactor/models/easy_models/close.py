import datetime
from typing import Type, TypeVar
from autobean.refactor.models.raw_models import close
from autobean.refactor.models.raw_models.close import CloseLabel
from . import internal
from .account import Account
from .date import Date

internal.token_model(CloseLabel)

_Self = TypeVar('_Self', bound='Close')


@internal.tree_model
class Close(close.Close):
    date = internal.required_date_property(close.Close.raw_date)
    account = internal.required_string_property(close.Close.raw_account)

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, account: str) -> _Self:
        return cls.from_children(Date.from_value(date), Account.from_value(account))
