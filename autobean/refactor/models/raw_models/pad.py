from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .account import Account
from .date import Date

_Self = TypeVar('_Self', bound='Pad')


@internal.token_model
class PadLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'PAD'
    DEFAULT = 'pad'


@internal.tree_model
class Pad(base.RawTreeModel):
    RULE = 'pad'

    @final
    def __init__(self, token_store: base.TokenStore, date: Date, label: PadLabel, account: Account, source_account: Account):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._account = account
        self._source_account = source_account

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._source_account

    _date = internal.field[Date]()
    _label = internal.field[PadLabel]()
    _account = internal.field[Account]()
    _source_account = internal.field[Account]()

    raw_date = internal.required_node_property(_date)
    raw_account = internal.required_node_property(_account)
    raw_source_account = internal.required_node_property(_source_account)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._account),
            token_transformer.transform(self._source_account))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._account = token_transformer.transform(self._account)
        self._source_account = token_transformer.transform(self._source_account)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Pad)
            and self._account == other._account
            and self._source_account == other._source_account)

    @classmethod
    def from_children(cls: Type[_Self], date: Date, account: Account, source_account: Account) -> _Self:
        label = PadLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *account.detach(),
            punctuation.Whitespace.from_default(),
            *source_account.detach(),
        ])
        return cls(token_store, date, label, account, source_account)
