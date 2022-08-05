import datetime
from typing import Type, TypeVar
from . import internal
from .date import Date
from .account import Account
from .escaped_string import EscapedString
from .generated import note
from .generated.note import NoteLabel

_Self = TypeVar('_Self', bound='Note')


@internal.tree_model
class Note(note.Note):
    date = internal.required_date_property(note.Note.raw_date)
    account = internal.required_string_property(note.Note.raw_account)
    comment = internal.required_string_property(note.Note.raw_comment)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            comment: str,
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            EscapedString.from_value(comment))