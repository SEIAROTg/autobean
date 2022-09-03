import datetime
import itertools
from typing import Iterable, Mapping, Optional, Type, TypeVar
from . import internal, meta_item_internal
from .date import Date
from .account import Account
from .escaped_string import EscapedString
from .inline_comment import InlineComment
from .link import Link
from .tag import Tag
from .generated import document
from .generated.document import DocumentLabel
from .meta_value import MetaRawValue, MetaValue

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
            *,
            tags: Iterable[str] = (),
            links: Iterable[str] = (),
            inline_comment: Optional[str] = None,
            meta: Optional[Mapping[str, MetaValue | MetaRawValue]] = None,
    ) -> _Self:
        return cls.from_children(
            date=Date.from_value(date),
            account=Account.from_value(account),
            filename=EscapedString.from_value(filename),
            tags_links=itertools.chain(map(Tag.from_value, tags), map(Link.from_value, links)),
            inline_comment=InlineComment.from_value(inline_comment) if inline_comment is not None else None,
            meta=meta_item_internal.from_mapping(meta) if meta is not None else (),
        )
