import datetime
from typing import Type, TypeVar
from . import internal
from .account import Account
from .date import Date
from .generated import pad
from .generated.pad import PadLabel

_Self = TypeVar('_Self', bound='Pad')


@internal.tree_model
class Pad(pad.Pad):

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, account: str, source_account: str) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            Account.from_value(source_account))
