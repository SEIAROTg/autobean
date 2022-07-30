import datetime
from typing import Type, TypeVar
from . import internal
from .date import Date
from .account import Account
from .escaped_string import EscapedString
from .generated import document
from .generated.document import DocumentLabel

_Self = TypeVar('_Self', bound='Document')


@internal.tree_model
class Document(document.Document):
    date = internal.required_date_property(document.Document.raw_date)
    account = internal.required_string_property(document.Document.raw_account)
    filename = internal.required_string_property(document.Document.raw_filename)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            filename: str,
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            EscapedString.from_value(filename))
