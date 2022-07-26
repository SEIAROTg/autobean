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
        self._date = date
        self._label = label
        self._account = account
        self._number = number
        self._tilde = tilde
        self._tolerance = tolerance
        self._currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._currency

    _date = internal.field[Date]()
    _label = internal.field[BalanceLabel]()
    _account = internal.field[Account]()
    _number = internal.field[NumberExpr]()
    _tilde = internal.field[Optional[Tilde]]()
    _tolerance = internal.field[Optional[NumberExpr]]()
    _currency = internal.field[Currency]()
  
    raw_date = internal.required_node_property(_date)
    raw_account = internal.required_node_property(_account)
    raw_number = internal.required_node_property(_number)
    raw_tilde = internal.optional_node_property(_tilde, floating=internal.Floating.LEFT)
    raw_tolerance = internal.optional_node_property(_tolerance, floating=internal.Floating.LEFT)
    raw_currency = internal.required_node_property(_currency)
    
    @raw_tolerance.creator
    def __raw_tolerance_creator(self, value: NumberExpr) -> None:
        tilde = Tilde.from_default()
        self.token_store.insert_after(self._number.last_token, [
            punctuation.Whitespace.from_default(),
            tilde,
            punctuation.Whitespace.from_default(),
            *value.detach(),
        ])
        value.reattach(self.token_store)
        self._tilde = tilde

    @raw_tolerance.remover
    def __raw_tolerance_remover(self, value: NumberExpr) -> None:
        start = self.token_store.get_next(self._number.last_token)
        assert start is not None
        self.token_store.splice([], start, value.last_token)
        self._tilde = None

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._account),
            self._number.clone(token_store, token_transformer),
            token_transformer.transform(self._tilde),
            self._tolerance.clone(token_store, token_transformer) if self._tolerance else None,
            token_transformer.transform(self._currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._account = token_transformer.transform(self._account)
        self._number.reattach(token_store, token_transformer)
        self._tilde = token_transformer.transform(self._tilde)
        if self._tolerance is not None:
            self._tolerance.reattach(token_store, token_transformer)
        self._currency = token_transformer.transform(self._currency)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Balance)
            and self._date == other._date
            and self._account == other._account
            and self._number == other._number
            and self._tolerance == other._tolerance
            and self._currency == other._currency)

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
