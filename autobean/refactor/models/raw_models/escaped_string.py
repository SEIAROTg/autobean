import re
from . import base


@base.token_model
class EscapedString(base.RawTokenModel):
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

    def __init__(self, raw_text: str, value: str) -> None:
        super().__init__(raw_text)
        self._value = value

    @classmethod
    def from_raw_text(cls, raw_text: str) -> 'EscapedString':
        return cls(raw_text, cls.unescape(raw_text[1:-1]))

    @classmethod
    def from_value(cls, value: str) -> 'EscapedString':
        return cls(f'"{cls.escape(value)}"', value)

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
    def raw_text(self, raw_text: str) -> None:
        self._update_raw_text(raw_text)
        self._value = self.unescape(raw_text[1:-1])

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
