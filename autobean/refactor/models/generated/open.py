# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

import datetime
from typing import Iterable, Mapping, Optional, Type, TypeVar, final
from .. import base, internal, meta_item_internal
from ..account import Account
from ..currency import Currency
from ..date import Date
from ..escaped_string import EscapedString
from ..meta_item import MetaItem
from ..meta_value import MetaRawValue, MetaValue
from ..punctuation import Comma, Eol, Newline, Whitespace

_Self = TypeVar('_Self', bound='Open')


@internal.token_model
class OpenLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'OPEN'
    DEFAULT = 'open'


@internal.tree_model
class Open(base.RawTreeModel):
    RULE = 'open'

    _date = internal.required_field[Date]()
    _label = internal.required_field[OpenLabel]()
    _account = internal.required_field[Account]()
    _currencies = internal.repeated_field[Currency](separators=(Comma.from_default(), Whitespace.from_default()), separators_before=(Whitespace.from_default(),))
    _booking = internal.optional_left_field[EscapedString](separators=(Whitespace.from_default(),))
    _eol = internal.required_field[Eol]()
    _meta = internal.repeated_field[MetaItem](separators=(Newline.from_default(), Whitespace.from_raw_text('    ')))

    raw_date = internal.required_node_property(_date)
    raw_account = internal.required_node_property(_account)
    raw_currencies = internal.repeated_node_property(_currencies)
    raw_booking = internal.optional_node_property(_booking)
    raw_meta = meta_item_internal.repeated_raw_meta_item_property(_meta)

    date = internal.required_date_property(raw_date)
    account = internal.required_string_property(raw_account)
    currencies = internal.repeated_string_property(raw_currencies, Currency)
    booking = internal.optional_string_property(raw_booking, EscapedString)
    meta = meta_item_internal.repeated_meta_item_property(_meta)

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            date: Date,
            label: OpenLabel,
            account: Account,
            currencies: internal.Repeated[Currency],
            booking: internal.Maybe[EscapedString],
            eol: Eol,
            meta: internal.Repeated[MetaItem],
    ):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._account = account
        self._currencies = currencies
        self._booking = booking
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
            self._account.clone(token_store, token_transformer),
            self._currencies.clone(token_store, token_transformer),
            self._booking.clone(token_store, token_transformer),
            self._eol.clone(token_store, token_transformer),
            self._meta.clone(token_store, token_transformer),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = self._date.reattach(token_store, token_transformer)
        self._label = self._label.reattach(token_store, token_transformer)
        self._account = self._account.reattach(token_store, token_transformer)
        self._currencies = self._currencies.reattach(token_store, token_transformer)
        self._booking = self._booking.reattach(token_store, token_transformer)
        self._eol = self._eol.reattach(token_store, token_transformer)
        self._meta = self._meta.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Open)
            and self._date == other._date
            and self._label == other._label
            and self._account == other._account
            and self._currencies == other._currencies
            and self._booking == other._booking
            and self._eol == other._eol
            and self._meta == other._meta
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
            date: Date,
            account: Account,
            currencies: Iterable[Currency] = (),
            booking: Optional[EscapedString] = None,
            meta: Iterable[MetaItem] = (),
    ) -> _Self:
        label = OpenLabel.from_default()
        repeated_currencies = cls._currencies.create_repeated(currencies)
        maybe_booking = cls._booking.create_maybe(booking)
        eol = Eol.from_default()
        repeated_meta = cls._meta.create_repeated(meta)
        tokens = [
            *date.detach(),
            Whitespace.from_default(),
            *label.detach(),
            Whitespace.from_default(),
            *account.detach(),
            *repeated_currencies.detach(),
            *maybe_booking.detach(),
            *eol.detach(),
            *repeated_meta.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        date.reattach(token_store)
        label.reattach(token_store)
        account.reattach(token_store)
        repeated_currencies.reattach(token_store)
        maybe_booking.reattach(token_store)
        eol.reattach(token_store)
        repeated_meta.reattach(token_store)
        return cls(token_store, date, label, account, repeated_currencies, maybe_booking, eol, repeated_meta)

    @classmethod
    def from_value(
            cls: Type[_Self],
            date: datetime.date,
            account: str,
            currencies: Iterable[str] = (),
            booking: Optional[str] = None,
            *,
            meta: Optional[Mapping[str, MetaValue | MetaRawValue]] = None,
    ) -> _Self:
        return cls.from_children(
            Date.from_value(date),
            Account.from_value(account),
            map(Currency.from_value, currencies),
            EscapedString.from_value(booking) if booking is not None else None,
            meta_item_internal.from_mapping(meta) if meta is not None else (),
        )
