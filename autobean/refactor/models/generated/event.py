# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

import datetime
from typing import Iterable, Mapping, Optional, Type, TypeVar, final
from .. import base, internal, meta_item_internal
from ..date import Date
from ..escaped_string import EscapedString
from ..inline_comment import InlineComment
from ..meta_item import MetaItem
from ..meta_value import MetaRawValue, MetaValue
from ..punctuation import Eol, Newline, Whitespace

_Self = TypeVar('_Self', bound='Event')


@internal.token_model
class EventLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'EVENT'
    DEFAULT = 'event'


@internal.tree_model
class Event(base.RawTreeModel):
    RULE = 'event'

    _date = internal.required_field[Date]()
    _label = internal.required_field[EventLabel]()
    _type = internal.required_field[EscapedString]()
    _description = internal.required_field[EscapedString]()
    _inline_comment = internal.optional_left_field[InlineComment](separators=(Whitespace.from_default(),))
    _eol = internal.required_field[Eol]()
    _meta = internal.repeated_field[MetaItem](separators=(Newline.from_default(),), default_indent='    ')

    raw_date = internal.required_node_property(_date)
    raw_type = internal.required_node_property(_type)
    raw_description = internal.required_node_property(_description)
    raw_inline_comment = internal.optional_node_property(_inline_comment)
    raw_meta = meta_item_internal.repeated_raw_meta_item_property(_meta)

    date = internal.required_date_property(raw_date)
    type = internal.required_string_property(raw_type)
    description = internal.required_string_property(raw_description)
    inline_comment = internal.optional_string_property(raw_inline_comment, InlineComment)
    meta = meta_item_internal.repeated_meta_item_property(_meta)

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            date: Date,
            label: EventLabel,
            type: EscapedString,
            description: EscapedString,
            inline_comment: internal.Maybe[InlineComment],
            eol: Eol,
            meta: internal.Repeated[MetaItem],
    ):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._type = type
        self._description = description
        self._inline_comment = inline_comment
        self._eol = eol
        self._meta = meta

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._meta.last_token

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self._date.clone(token_store, token_transformer),
            self._label.clone(token_store, token_transformer),
            self._type.clone(token_store, token_transformer),
            self._description.clone(token_store, token_transformer),
            self._inline_comment.clone(token_store, token_transformer),
            self._eol.clone(token_store, token_transformer),
            self._meta.clone(token_store, token_transformer),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = self._date.reattach(token_store, token_transformer)
        self._label = self._label.reattach(token_store, token_transformer)
        self._type = self._type.reattach(token_store, token_transformer)
        self._description = self._description.reattach(token_store, token_transformer)
        self._inline_comment = self._inline_comment.reattach(token_store, token_transformer)
        self._eol = self._eol.reattach(token_store, token_transformer)
        self._meta = self._meta.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Event)
            and self._date == other._date
            and self._label == other._label
            and self._type == other._type
            and self._description == other._description
            and self._inline_comment == other._inline_comment
            and self._eol == other._eol
            and self._meta == other._meta
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
            date: Date,
            type: EscapedString,
            description: EscapedString,
            *,
            inline_comment: Optional[InlineComment] = None,
            meta: Iterable[MetaItem] = (),
    ) -> _Self:
        label = EventLabel.from_default()
        maybe_inline_comment = cls._inline_comment.create_maybe(inline_comment)
        eol = Eol.from_default()
        repeated_meta = cls._meta.create_repeated(meta)
        tokens = [
            *date.detach(),
            Whitespace.from_default(),
            *label.detach(),
            Whitespace.from_default(),
            *type.detach(),
            Whitespace.from_default(),
            *description.detach(),
            *maybe_inline_comment.detach(),
            *eol.detach(),
            *repeated_meta.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        date.reattach(token_store)
        label.reattach(token_store)
        type.reattach(token_store)
        description.reattach(token_store)
        maybe_inline_comment.reattach(token_store)
        eol.reattach(token_store)
        repeated_meta.reattach(token_store)
        return cls(token_store, date, label, type, description, maybe_inline_comment, eol, repeated_meta)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            type: str,
            description: str,
            *,
            inline_comment: Optional[str] = None,
            meta: Optional[Mapping[str, MetaValue | MetaRawValue]] = None,
    ) -> _Self:
        return cls.from_children(
            date=Date.from_value(date),
            type=EscapedString.from_value(type),
            description=EscapedString.from_value(description),
            inline_comment=InlineComment.from_value(inline_comment) if inline_comment is not None else None,
            meta=meta_item_internal.from_mapping(meta) if meta is not None else (),
        )
