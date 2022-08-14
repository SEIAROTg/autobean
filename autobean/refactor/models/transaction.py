import datetime
import itertools
from typing import Iterable, Mapping, Optional, Type, TypeVar
from . import base, internal, meta_item_internal
from .date import Date
from .escaped_string import EscapedString
from .link import Link
from .meta_value import MetaRawValue, MetaValue
from .meta_item import MetaItem
from .posting import Posting
from .tag import Tag
from .transaction_flag import TransactionFlag
from .generated import transaction

_Self = TypeVar('_Self', bound='Transaction')


@internal.tree_model
class Transaction(transaction.Transaction):

    @classmethod
    def from_parsed_children(cls: Type[_Self], token_store: base.TokenStore, *children: Optional[base.RawModel]) -> _Self:
        date, flag, string0, string1, string2, tags_links, eol, meta, postings = children
        assert isinstance(string1, internal.Maybe)
        assert isinstance(string2, internal.Maybe)
        if string1.inner is not None and string2.inner is None:
            string1, string2 = string0, string1
        return super().from_parsed_children(token_store, date, flag, string0, string1, string2, tags_links, eol, meta, postings)

    @internal.custom_node_property
    def raw_payee(self) -> Optional[EscapedString]:
        return self.raw_string1

    @raw_payee.setter
    def __raw_payee(self, value: Optional[EscapedString]) -> None:
        if value is not None and self.raw_narration is None:
            self.raw_narration = EscapedString.from_value('') 
        self.raw_string1 = value

    @internal.custom_node_property
    def raw_narration(self) -> Optional[EscapedString]:
        return self.raw_string2

    @raw_narration.setter
    def __raw_narration(self, value: Optional[EscapedString]) -> None:
        if value is None and self.raw_payee is not None:
            value = EscapedString.from_value('')
        self.raw_string2 = value

    payee = internal.optional_string_property(raw_payee, EscapedString)
    narration = internal.optional_string_property(raw_narration, EscapedString)
    tags = internal.repeated_string_property(transaction.Transaction.raw_tags_links, Tag)
    links = internal.repeated_string_property(transaction.Transaction.raw_tags_links, Link)

    @classmethod
    def from_children(  # type: ignore[override]
            cls: Type[_Self],
            date: Date,
            flag: TransactionFlag,
            payee: Optional[EscapedString],
            narration: Optional[EscapedString],
            tags_links: Iterable[Link | Tag],
            meta: Iterable[MetaItem],
            postings: Iterable[Posting],
    ) -> _Self:
        if payee is not None and narration is None:
            narration = EscapedString.from_value('')
        return super().from_children(
            date,
            flag,
            None,
            payee,
            narration,
            tags_links,
            meta,
            postings,
        )

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            payee: Optional[str],
            narration: Optional[str],
            postings: Iterable[Posting],
            *,
            flag: str = '*',
            tags: Iterable[str] = (),
            links: Iterable[str] = (),
            meta: Optional[Mapping[str, MetaRawValue | MetaValue]] = None,
    ) -> _Self:
        return cls.from_children(
            date=Date.from_value(date),
            flag=TransactionFlag.from_value(flag),
            payee=EscapedString.from_value(payee) if payee is not None else None,
            narration=EscapedString.from_value(narration) if narration is not None else None,
            tags_links=itertools.chain(map(Tag.from_value, tags), map(Link.from_value, links)),
            meta=meta_item_internal.from_mapping(meta) if meta is not None else (),
            postings=postings,
        )
