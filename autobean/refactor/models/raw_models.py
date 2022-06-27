import abc
import re
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


def _token_model(cls: _T) -> _T:
    TOKEN_MODELS.append(cls)
    return cls


def _tree_model(cls: _U) -> _U:
    TREE_MODELS.append(cls)
    return cls


@_token_model
class EscapedString(RawTokenModel):
    RULE = 'ESCAPED_STRING'
    # See: https://github.com/beancount/beancount/blob/d841487ccdda04c159de86b1186e7c2ea997a3e2/beancount/parser/tokens.c#L102
    __ESCAPE_MAP = {
        '\n': 'n',
        '\t': 't',
        '\r': 'r',
        '\f': 'f',
        '\b': 'b',
        '"': '"',
        '\\': '\\',
    }
    __ESCAPE_PATTERN = re.compile(r'[\\"]')
    __ESCAPE_PATTERN_AGGRESSIVE = re.compile(
        '|'.join(map(re.escape, __ESCAPE_MAP.keys())))
    __UNESCAPE_MAP = {value: key for key, value in __ESCAPE_MAP.items()}
    __UNESCAPE_PATTERN = re.compile(r'\\(.)')

    def __init__(self, raw_text: str) -> None:
        super().__init__(raw_text)
        self._value = self.unescape(self.raw_text[1:-1])

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        self._update_raw_text(f'"{self.escape(value)}"')

    @property
    def raw_text(self) -> str:
        return super().raw_text

    @raw_text.setter
    def raw_text(self, value: str) -> None:
        self._update_raw_text(value)
        self._value = self.unescape(self.raw_text[1:-1])

    @classmethod
    def escape(cls, s: str, aggressive: bool = False) -> str:
        pattern = cls.__ESCAPE_PATTERN_AGGRESSIVE if aggressive else cls.__ESCAPE_PATTERN
        return re.sub(
            pattern,
            lambda c: '\\' + cls.__ESCAPE_MAP[c.group(0)],
            s)

    @classmethod
    def unescape(cls, s: str) -> str:
        return re.sub(
            cls.__UNESCAPE_PATTERN,
            lambda c: cls.__UNESCAPE_MAP.get(c.group(1), c.group(1)),
            s)


@_token_model
class Newline(RawTokenModel):
    RULE = '_NL'


@_token_model
class Indent(RawTokenModel):
    RULE = 'INDENT'


@_token_model
class Whitespace(RawTokenModel):
    RULE = 'WS_INLINE'


@_token_model
class Comment(RawTokenModel):
    RULE = 'COMMENT'


@_token_model
class OptionLabel(RawTokenModel):
    RULE = 'OPTION'


@_tree_model
class Option(RawTreeModel):
    RULE = 'option'

    def __init__(self, token_store: token_store_lib.TokenStore, label: OptionLabel, key: EscapedString, value: EscapedString):
        super().__init__(token_store)
        self._label = label
        self._key = key
        self._value = value

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self._value

    @property
    def raw_key(self) -> EscapedString:
        return self._key

    @property
    def raw_value(self) -> EscapedString:
        return self._value


@_token_model
class IncludeLabel(RawTokenModel):
    RULE = 'INCLUDE'


@_tree_model
class Include(RawTreeModel):
    RULE = 'include'

    def __init__(self, token_store: token_store_lib.TokenStore, label: IncludeLabel, filename: EscapedString):
        super().__init__(token_store)
        self._label = label
        self._filename = filename

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self._filename

    @property
    def raw_filename(self) -> EscapedString:
        return self._filename


@_token_model
class PluginLabel(RawTokenModel):
    RULE = 'PLUGIN'


@_tree_model
class Plugin(RawTreeModel):
    RULE = 'plugin'

    def __init__(self, token_store: token_store_lib.TokenStore, label: PluginLabel, name: EscapedString, config: Optional[EscapedString]):
        super().__init__(token_store)
        self._label = label
        self._name = name
        self._config = config

    @property
    def first_token(self) -> token_store_lib.Token:
        return self._label

    @property
    def last_token(self) -> token_store_lib.Token:
        return self._config or self._name

    @property
    def raw_name(self) -> EscapedString:
        return self._name

    @property
    def raw_config(self) -> Optional[EscapedString]:
        return self._config


@_tree_model
class File(RawTreeModel):
    RULE = 'file'

    def __init__(self, token_store: token_store_lib.TokenStore, *directives: RawTreeModel):
        super().__init__(token_store)
        self._directives = list(directives)

    @property
    def first_token(self) -> Optional[token_store_lib.Token]:
        return self._token_store.get_first()

    @property
    def last_token(self) -> Optional[token_store_lib.Token]:
        return self._token_store.get_last()
