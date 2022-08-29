# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

import decimal
from typing import Optional, Type, TypeVar, final
from .. import base, internal
from ..currency import Currency
from ..number_expr import NumberExpr
from ..punctuation import Whitespace

_Self = TypeVar('_Self', bound='CompoundAmount')


@internal.token_model
class Hash(internal.SimpleDefaultRawTokenModel):
    RULE = 'HASH'
    DEFAULT = '#'


@internal.tree_model
class CompoundAmount(base.RawTreeModel):
    RULE = 'compound_amount'

    _number_per = internal.optional_right_field[NumberExpr](separators=(Whitespace.from_default(),))
    _hash = internal.required_field[Hash]()
    _number_total = internal.optional_left_field[NumberExpr](separators=(Whitespace.from_default(),))
    _currency = internal.required_field[Currency]()

    raw_number_per = internal.optional_node_property(_number_per)
    raw_number_total = internal.optional_node_property(_number_total)
    raw_currency = internal.required_node_property(_currency)

    number_per = internal.optional_decimal_property(raw_number_per, NumberExpr)
    number_total = internal.optional_decimal_property(raw_number_total, NumberExpr)
    currency = internal.required_string_property(raw_currency)

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            number_per: internal.Maybe[NumberExpr],
            hash: Hash,
            number_total: internal.Maybe[NumberExpr],
            currency: Currency,
    ):
        super().__init__(token_store)
        self._number_per = number_per
        self._hash = hash
        self._number_total = number_total
        self._currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._number_per.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._currency.last_token

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            self._number_per.clone(token_store, token_transformer),
            self._hash.clone(token_store, token_transformer),
            self._number_total.clone(token_store, token_transformer),
            self._currency.clone(token_store, token_transformer),
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._number_per = self._number_per.reattach(token_store, token_transformer)
        self._hash = self._hash.reattach(token_store, token_transformer)
        self._number_total = self._number_total.reattach(token_store, token_transformer)
        self._currency = self._currency.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, CompoundAmount)
            and self._number_per == other._number_per
            and self._hash == other._hash
            and self._number_total == other._number_total
            and self._currency == other._currency
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
            number_per: Optional[NumberExpr],
            number_total: Optional[NumberExpr],
            currency: Currency,
    ) -> _Self:
        maybe_number_per = cls._number_per.create_maybe(number_per)
        hash = Hash.from_default()
        maybe_number_total = cls._number_total.create_maybe(number_total)
        tokens = [
            *maybe_number_per.detach(),
            *hash.detach(),
            *maybe_number_total.detach(),
            Whitespace.from_default(),
            *currency.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        maybe_number_per.reattach(token_store)
        hash.reattach(token_store)
        maybe_number_total.reattach(token_store)
        currency.reattach(token_store)
        return cls(token_store, maybe_number_per, hash, maybe_number_total, currency)

    @classmethod
    def from_value(
            cls: Type[_Self],
            number_per: Optional[decimal.Decimal],
            number_total: Optional[decimal.Decimal],
            currency: str,
    ) -> _Self:
        return cls.from_children(
            NumberExpr.from_value(number_per) if number_per is not None else None,
            NumberExpr.from_value(number_total) if number_total is not None else None,
            Currency.from_value(currency),
        )
