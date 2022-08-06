import datetime
import itertools
from typing import Iterable, Type, TypeVar
from . import internal
from .date import Date
from .account import Account
from .escaped_string import EscapedString
from .link import Link
from .tag import Tag
from .generated import document
from .generated.document import DocumentLabel

_Self = TypeVar('_Self', bound='Document')


@internal.tree_model
class Document(document.Document):
    tags = internal.repeated_string_property(document.Document.raw_tags_links, Tag)
    links = internal.repeated_string_property(document.Document.raw_tags_links, Link)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            filename: str,
            tags: Iterable[str] = (),
            links: Iterable[str] = (),
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            EscapedString.from_value(filename),
            itertools.chain(map(Tag.from_value, tags), map(Link.from_value, links)),
        )
