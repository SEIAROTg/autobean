import re
from typing import Type, TypeVar, final
from . import base, internal

_INDENT_SPLIT_RE = re.compile(';\s*')
_Self = TypeVar('_Self', bound='BlockComment')


@internal.token_model
class BlockComment(base.RawTokenModel):
    RULE = 'BLOCK_COMMENT'

    @final
    def __init__(self, raw_text: str, indent: str, value: str) -> None:
        super().__init__(raw_text)
        self._value = value
        self._indent = indent

    @property
    def raw_text(self) -> str:
        return super().raw_text

    @raw_text.setter
    def raw_text(self, raw_text: str) -> None:
        self._update_raw_text(raw_text)
        self._indent, self._value = self._parse_value(raw_text)

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str) -> None:
        self._value = value
        self._update_raw_text(self._format_value(self._indent, value))

    @property
    def indent(self) -> str:
        return self._indent

    @indent.setter
    def indent(self, indent: str) -> None:
        self._indent = indent
        self._update_raw_text(self._format_value(indent, self._value))

    @classmethod
    def from_value(cls: Type[_Self], value: str, *, indent: str = '') -> _Self:
        return cls(cls._format_value(indent, value), indent, value)

    @classmethod
    def from_raw_text(cls: Type[_Self], raw_text: str) -> _Self:
        indent, value = cls._parse_value(raw_text)
        return cls(raw_text, indent, value)

    @classmethod
    def _parse_value(cls, raw_text: str) -> tuple[str, str]:
        indents, values = zip(*(
            tuple(_INDENT_SPLIT_RE.split(line, maxsplit=1))
            for line in raw_text.splitlines(keepends=True)
        ))
        return indents[0], ''.join(values)

    @classmethod
    def _format_value(cls, indent: str, value: str) -> str:
        return ''.join(
            f'{indent}; {line}' if line else f'{indent};'
            for line in value.splitlines(keepends=True) or ['']
        )

    def _clone(self: 'BlockComment') -> 'BlockComment':
        return type(self)(self.raw_text, self.indent, self.value)
