import abc
from typing import ClassVar, Optional, Type, TypeVar
from autobean.refactor import token_store as token_store_lib


class RawModel(abc.ABC):
    RULE: ClassVar[str]

    @property
    @abc.abstractmethod
    def token_store(self) -> Optional[token_store_lib.TokenStore]:
        ...

    @property
    @abc.abstractmethod
    def first_token(self) -> Optional[token_store_lib.Token]:
        ...

    @property
    @abc.abstractmethod
    def last_token(self) -> Optional[token_store_lib.Token]:
        ...


class RawTokenModel(token_store_lib.Token, RawModel):
    def __init__(self, raw_text: str) -> None:
        super().__init__(raw_text)

    @property
    def token_store(self) -> Optional[token_store_lib.TokenStore]:
        return self.store_handle.store if self.store_handle else None

    @property
    def first_token(self) -> Optional[token_store_lib.Token]:
        return self

    @property
    def last_token(self) -> Optional[token_store_lib.Token]:
        return self


class RawTreeModel(RawModel):
    def __init__(self, token_store: token_store_lib.TokenStore) -> None:
        super().__init__()
        self._token_store = token_store

    @property
    def token_store(self) -> token_store_lib.TokenStore:
        return self._token_store


TOKEN_MODELS: list[Type[RawTokenModel]] = []
TREE_MODELS: list[Type[RawTreeModel]] = []
_T = TypeVar('_T', bound=Type[RawTokenModel])
_U = TypeVar('_U', bound=Type[RawTreeModel])


def token_model(cls: _T) -> _T:
    TOKEN_MODELS.append(cls)
    return cls


def tree_model(cls: _U) -> _U:
    TREE_MODELS.append(cls)
    return cls


@token_model
class Newline(RawTokenModel):
    RULE = '_NL'


@token_model
class Indent(RawTokenModel):
    RULE = 'INDENT'


@token_model
class Whitespace(RawTokenModel):
    RULE = 'WS_INLINE'


@token_model
class Comment(RawTokenModel):
    RULE = 'COMMENT'
