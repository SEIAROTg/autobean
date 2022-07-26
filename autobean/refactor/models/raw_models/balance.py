from typing import Optional, TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .account import Account
from .currency import Currency
from .date import Date
from .number_expr import NumberExpr
from .tolerance import Tolerance

_Self = TypeVar('_Self', bound='Balance')


@internal.token_model
class BalanceLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'BALANCE'
    DEFAULT = 'balance'


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
            tolerance: Optional[Tolerance],
            currency: Currency,
    ):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._account = account
        self._number = number
        self._tolerance = tolerance
        self._currency = currency

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._currency

    _date = internal.required_field[Date]()
    _label = internal.required_field[BalanceLabel]()
    _account = internal.required_field[Account]()
    _number = internal.required_field[NumberExpr]()
    _tolerance = internal.optional_field[Tolerance](floating=internal.Floating.LEFT)
    _currency = internal.required_field[Currency]()
  
    raw_date = internal.required_node_property(_date)
    raw_account = internal.required_node_property(_account)
    raw_number = internal.required_node_property(_number)
    raw_tolerance = internal.optional_node_property(_tolerance)
    raw_currency = internal.required_node_property(_currency)
    
    @raw_tolerance.creator
    def __raw_tolerance_creator(self, value: Tolerance) -> None:
        self.token_store.insert_after(self._number.last_token, [
            punctuation.Whitespace.from_default(),
            *value.detach(),
        ])
        value.reattach(self.token_store)

    @raw_tolerance.remover
    def __raw_tolerance_remover(self, value: Tolerance) -> None:
        start = self.token_store.get_next(self._number.last_token)
        assert start is not None
        self.token_store.splice([], start, value.last_token)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._account),
            self._number.clone(token_store, token_transformer),
            self._tolerance.clone(token_store, token_transformer) if self._tolerance else None,
            token_transformer.transform(self._currency))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._account = token_transformer.transform(self._account)
        self._number.reattach(token_store, token_transformer)
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
            number: NumberExpr,
            tolerance: Optional[Tolerance],
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
            *number.detach(),
            punctuation.Whitespace.from_default(),
        ]
        if tolerance is not None:
            tokens.extend([
                *tolerance.detach(),
                punctuation.Whitespace.from_default(),
            ])
        tokens.extend(currency.detach())
        token_store = base.TokenStore.from_tokens(tokens)
        number.reattach(token_store)
        if tolerance is not None:
            tolerance.reattach(token_store)
        return cls(token_store, date, label, account, number, tolerance, currency)
