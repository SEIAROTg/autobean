import datetime
from typing import Type, TypeVar
from autobean.refactor.models.raw_models import event
from autobean.refactor.models.raw_models.event import EventLabel
from . import internal
from .escaped_string import EscapedString
from .date import Date

internal.token_model(EventLabel)

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
