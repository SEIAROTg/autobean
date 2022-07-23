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
        self.raw_date = date
        self._label = label
        self.raw_account = account

    @property
    def first_token(self) -> base.RawTokenModel:
        return self.raw_date

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_account

    @internal.required_node_property
    def raw_date(self) -> Date:
        pass

    @internal.required_node_property
    def raw_account(self) -> Account:
        pass

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
            token_transformer.transform(self.raw_date),
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_account))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        type(self).raw_date.reset(self, token_transformer.transform(self.raw_date))
        self._label = token_transformer.transform(self._label)
        type(self).raw_account.reset(self, token_transformer.transform(self.raw_account))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Close)
            and self.raw_account == other.raw_account)

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
