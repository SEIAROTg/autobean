from typing import TypeVar, Type, final
from autobean.refactor.models.raw_models import punctuation
from . import base
from . import internal
from .account import Account
from .date import Date

_Self = TypeVar('_Self', bound='Close')


@internal.token_model
class CloseLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'CLOSE'
    DEFAULT = 'close'


@internal.tree_model
class Close(base.RawTreeModel):
    RULE = 'close'

    @final
    def __init__(self, token_store: base.TokenStore, date: Date, label: CloseLabel, account: Account):
        super().__init__(token_store)
        self._date = date
        self._label = label
        self._account = account

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._account

    _date = internal.required_field[Date]()
    _label = internal.required_field[CloseLabel]()
    _account = internal.required_field[Account]()

    raw_date = internal.required_node_property(_date)
    raw_account = internal.required_node_property(_account)

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self._date),
            token_transformer.transform(self._label),
            token_transformer.transform(self._account))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._date = token_transformer.transform(self._date)
        self._label = token_transformer.transform(self._label)
        self._account = token_transformer.transform(self._account)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Close)
            and self._account == other._account)

    @classmethod
    def from_children(cls: Type[_Self], date: Date, account: Account) -> _Self:
        label = CloseLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            *date.detach(),
            punctuation.Whitespace.from_default(),
            label,
            punctuation.Whitespace.from_default(),
            *account.detach(),
        ])
        return cls(token_store, date, label, account)
