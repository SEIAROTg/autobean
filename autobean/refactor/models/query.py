import datetime
from typing import Type, TypeVar
from . import internal
from .escaped_string import EscapedString
from .date import Date
from .generated import query
from .generated.query import QueryLabel

_Self = TypeVar('_Self', bound='Query')


@internal.tree_model
class Query(query.Query):

    @classmethod
    def from_value(cls: Type[_Self], date: datetime.date, name: str, query_string: str) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            EscapedString.from_value(name),
            EscapedString.from_value(query_string))
