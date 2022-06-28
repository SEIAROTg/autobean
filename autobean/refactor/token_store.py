import bisect
import dataclasses
from typing import Any, Collection, Iterable, Iterator, Optional


@dataclasses.dataclass(frozen=True)
class Position:
    position: int
    line: int
    column: int

    def __add__(self, other: Any) -> 'Position':
        if not isinstance(other, Position):
            raise TypeError(
                f"unsupported operand type(s) for +: {type(self).__name__!r} "
                f"and {type(other).__name__!r}.")
        if other.line:
            column = other.column
        else:
            column = self.column + other.column
        return Position(
            position=self.position + other.position,
            line=self.line + other.line,
            column=column)  # not commutative!


class Token:
    _raw_text: str
    store_handle: Optional['_Handle']

    def __init__(self, raw_text: str) -> None:
        self._raw_text = raw_text
        self.store_handle = None

    @property
    def raw_text(self) -> str:
        return self._raw_text

    @raw_text.setter
    def raw_text(self, value: str) -> None:
        self._update_raw_text(value)

    # property setter override is painful. use setter method instead.
    def _update_raw_text(self, value: str) -> None:
        self._raw_text = value
        if self.store_handle:
            self.store_handle.store.update(self)

    def get_next(self) -> Optional['Token']:
        handle = _check_store_handle(self)
        return handle.store.get_next(self)


@dataclasses.dataclass(eq=False)
class _Handle:
    store: 'TokenStore'
    index: int
    position: Position


def _check_store_handle(token: Token) -> _Handle:
    if not token.store_handle:
        raise ValueError('Token is not in a store.')
    return token.store_handle


def _token_size(token: Token) -> Position:
    return Position(
        position=len(token.raw_text),
        line=token.raw_text.count('\n'),
        column=len(token.raw_text) - token.raw_text.rfind('\n') - 1)


class TokenStore:
    """Storage for tokens allowing insertion, deletion and lookup by position."""

    _tokens: list[Token]
    _end: Position

    def __init__(self) -> None:
        self._tokens = []
        self._end = Position(0, 0, 0)

    @classmethod
    def from_tokens(cls, tokens: Iterable[Token]) -> 'TokenStore':
        for token in tokens:
            if token.store_handle:
                raise ValueError('Token already in a store.')
        store = TokenStore()
        for token in tokens:
            token.store_handle = _Handle(
                store=store, index=0, position=Position(0, 0, 0))
        store._tokens.extend(tokens)
        store._update_token_handles()
        return store

    def _update_token_handles(self, from_index: int = 0) -> None:
        if from_index:
            prev = self._tokens[from_index - 1]
            position = _check_store_handle(prev).position + _token_size(prev)
        else:
            position = Position(0, 0, 0)
        for index in range(from_index, len(self._tokens)):
            token = self._tokens[index]
            handle = _check_store_handle(token)
            handle.position = position
            handle.index = index
            position += _token_size(token)
        self._end = position

    def _splice(self, tokens: Collection[Token], start: int, end: int) -> None:
        for token in tokens:
            handle = token.store_handle
            if handle and not (handle.store is self and start <= handle.index <= end):
                raise ValueError('Token already in a store.')
        for token in tokens:
            token.store_handle = _Handle(store=self, index=0, position=Position(0, 0, 0))
        self._tokens[start:end] = tokens
        self._update_token_handles(start)

    def splice(self, tokens: Collection[Token], ref: Optional[Token], del_end: Optional[Token] = None) -> None:
        start = _check_store_handle(ref).index if ref else 0
        end = _check_store_handle(del_end).index + 1 if del_end else start
        self._splice(tokens, start, end)

    def insert_after(self, ref: Optional[Token], tokens: Collection[Token]) -> None:
        if ref is None:
            start = 0
        else:
            start = _check_store_handle(ref).index + 1
        self._splice(tokens, start, start)

    def insert_before(self, ref: Optional[Token], tokens: Collection[Token]) -> None:
        self.splice(tokens, ref)

    def update(self, token: Token) -> None:
        handle = _check_store_handle(token)
        self._update_token_handles(handle.index + 1)

    def replace(self, token: Token, repl: Token) -> None:
        self.splice([repl], token, token)

    def remove(self, start: Token, end: Optional[Token] = None) -> None:
        self.splice([], start, end or start)

    def get_position(self, token: Token) -> Position:
        handle = _check_store_handle(token)
        return handle.position

    def get_by_position(self, position: int) -> Token:
        index = bisect.bisect_left(
            self._tokens, position, key=lambda t: _check_store_handle(t).position.position)
        if index >= len(self._tokens) or _check_store_handle(self._tokens[index]).position.position != position:
            raise KeyError(f'No token found at position {position}.')
        return self._tokens[index]

    def find_by_line(self, line: int) -> Iterator[Token]:  # zero-based
        index = bisect.bisect_left(
            self._tokens, line, key=lambda t: _check_store_handle(t).position.line)
        while index < len(self._tokens):
            handle = _check_store_handle(self._tokens[index])
            if handle.position.line > line:
                break
            yield self._tokens[index]

    def get_prev(self, token: Token) -> Optional[Token]:
        handle = _check_store_handle(token)
        if handle.index:
            return self._tokens[handle.index - 1]
        else:
            return None

    def get_next(self, token: Token) -> Optional[Token]:
        handle = _check_store_handle(token)
        if handle.index < len(self._tokens) - 1:
            return self._tokens[handle.index + 1]
        else:
            return None

    def get_first(self) -> Optional[Token]:
        return self._tokens[0] if self._tokens else None

    def get_last(self) -> Optional[Token]:
        return self._tokens[-1] if self._tokens else None

    def __iter__(self) -> Iterator[Token]:
        yield from self._tokens

    def __len__(self) -> int:
        return len(self._tokens)

    @ property
    def size(self) -> int:
        return self._end.position
