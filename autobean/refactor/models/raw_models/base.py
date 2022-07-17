import abc
from typing import Any, ClassVar, Optional, Type, TypeVar
from autobean.refactor import token_store as token_store_lib

_T = TypeVar('_T', bound='RawTokenModel')
TokenStore = token_store_lib.TokenStore['RawTokenModel']


class RawModel(abc.ABC):
    RULE: ClassVar[str]

    @property
    @abc.abstractmethod
    def token_store(self) -> Optional[TokenStore]:
        ...

    @property
    @abc.abstractmethod
    def first_token(self) -> Optional['RawTokenModel']:
        ...

    @property
    @abc.abstractmethod
    def last_token(self) -> Optional['RawTokenModel']:
        ...


class RawTokenModel(token_store_lib.Token, RawModel):
    def __init__(self, raw_text: str) -> None:
        super().__init__(raw_text)

    @classmethod
    def from_raw_text(cls: Type[_T], raw_text: str) -> _T:
        return cls(raw_text)

    @property
    def token_store(self) -> Optional[TokenStore]:
        return self.store_handle.store if self.store_handle else None

    @property
    def first_token(self) -> 'RawTokenModel':
        return self

    @property
    def last_token(self) -> 'RawTokenModel':
        return self


class RawTreeModel(RawModel):
    def __init__(self, token_store: TokenStore) -> None:
        super().__init__()
        self._token_store = token_store

    @property
    def token_store(self) -> TokenStore:
        return self._token_store



