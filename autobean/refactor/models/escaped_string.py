import re
from . import internal


@internal.token_model
class EscapedString(internal.SingleValueRawTokenModel[str]):
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

    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        return cls.unescape(raw_text[1:-1])
    
    @classmethod
    def _format_value(cls, value: str) -> str:
        return f'"{cls.escape(value)}"'

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
