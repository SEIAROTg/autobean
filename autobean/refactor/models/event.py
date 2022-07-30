import datetime
from typing import Type, TypeVar
from . import internal
from .escaped_string import EscapedString
from .date import Date
from .generated import event
from .generated.event import EventLabel

_Self = TypeVar('_Self', bound='Event')


@internal.tree_model
class Event(event.Event):
    date = internal.required_date_property(event.Event.raw_date)
    type = internal.required_string_property(event.Event.raw_type)
    description = internal.required_string_property(event.Event.raw_description)

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, type: str, description: str) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            EscapedString.from_value(type),
            EscapedString.from_value(description))
