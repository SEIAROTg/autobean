from typing import Optional, TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .account import Account
from .currency import Currency
from .date import Date
from .number_expr import NumberExpr

_Self = TypeVar('_Self', bound='Balance')


@internal.token_model
class BalanceLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'BALANCE'
    DEFAULT = 'balance'


@internal.token_model
class Tilde(internal.SimpleDefaultRawTokenModel):
    RULE = 'TILDE'
    DEFAULT = '~'


@internal.tree_model
class Balance(base.RawTreeModel):
    RULE = 'balance'

    @final
    def __init__(
            self,
            token_store: base.TokenStore,
            date: Date,
            label: BalanceLabel,
            account: Account,
            number: NumberExpr,
            tilde: Optional[Tilde],
            tolerance: Optional[NumberExpr],
            currency: Currency,
    ):
        super().__init__(token_store)
        self.raw_date = date
        self._label = label
        self.raw_account = account
        self.raw_number = number
        self._tilde = tilde
        self.raw_tolerance = tolerance
        self.raw_currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_currency

    @internal.required_node_property
    def raw_date(self) -> Date:
        pass

    @internal.required_node_property
    def raw_account(self) -> Account:
        pass

    @internal.required_node_property
    def raw_number(self) -> NumberExpr:
        pass

    @internal.optional_node_property(floating=internal.Floating.LEFT)
    def raw_tolerance(self) -> NumberExpr:
        pass

    @raw_tolerance.creator
    def __raw_tolerance_creator(self, value: NumberExpr) -> None:
        tilde = Tilde.from_default()
        self.token_store.insert_after(self.raw_number.last_token, [
            punctuation.Whitespace.from_default(),
            tilde,
            punctuation.Whitespace.from_default(),
            *value.detach(),
        ])
        value.reattach(self.token_store)
        self._tilde = tilde

    @raw_tolerance.remover
    def __raw_tolerance_remover(self, value: NumberExpr) -> None:
        start = self.token_store.get_next(self.raw_number.last_token)
        assert start is not None
        self.token_store.splice([], start, value.last_token)
        self._tilde = None

    @internal.required_node_property
    def raw_currency(self) -> Currency:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_date),
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_account),
            self.raw_number.clone(token_store, token_transformer),
            token_transformer.transform(self._tilde),
            self.raw_tolerance.clone(token_store, token_transformer) if self.raw_tolerance else None,
            token_transformer.transform(self.raw_currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_date.reset(self, token_transformer.transform(self.raw_date))
        self._label = token_transformer.transform(self._label)
        type(self).raw_account.reset(self, token_transformer.transform(self.raw_account))
        self.raw_number.reattach(token_store, token_transformer)
        self._tilde = token_transformer.transform(self._tilde)
        if self.raw_tolerance is not None:
            self.raw_tolerance.reattach(token_store, token_transformer)
        type(self).raw_currency.reset(self, token_transformer.transform(self.raw_currency))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Balance)
            and self.raw_date == other.raw_date
            and self.raw_account == other.raw_account
            and self.raw_number == other.raw_number
            and self.raw_tolerance == other.raw_tolerance
            and self.raw_currency == other.raw_currency)

    @classmethod
    def from_children(
            cls: Type[_Self],
            date: Date,
            account: Account,
            number_expr: NumberExpr,
            tolerance: Optional[NumberExpr],
            currency: Currency,
    ) -> _Self:
        label = BalanceLabel.from_default()
        tokens = [
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *account.detach(),
            punctuation.Whitespace.from_default(),
            *number_expr.detach(),
            punctuation.Whitespace.from_default(),
        ]
        if tolerance is not None:
            tilde = Tilde.from_default()
            tokens.extend([
                tilde,
                punctuation.Whitespace.from_default(),
                *tolerance.detach(),
                punctuation.Whitespace.from_default(),
            ])
        else:
            tilde = None
        tokens.extend(currency.detach())
        token_store = base.TokenStore.from_tokens(tokens)
        number_expr.reattach(token_store)
        if tolerance is not None:
            tolerance.reattach(token_store)
        return cls(token_store, date, label, account, number_expr, tilde, tolerance, currency)
