import bisect
import dataclasses
from typing import Any, Collection, Generic, Iterable, Iterator, Optional, Type, TypeVar

_T = TypeVar('_T', bound='Token')
_Self = TypeVar('_Self', bound='TokenStore')


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


class TokenStore(Generic[_T]):
    """Storage for tokens allowing insertion, deletion and lookup by position."""

    _tokens: list[_T]
    _end: Position

    def __init__(self) -> None:
        self._tokens = []
        self._end = Position(0, 0, 0)

    @classmethod
    def from_tokens(cls: Type[_Self], tokens: Iterable[_T]) -> _Self:
        for token in tokens:
            if token.store_handle:
                raise ValueError('Token already in a store.')
        store = cls()
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

    def _splice(self, tokens: Collection[_T], start: int, end: int) -> None:
        for token in tokens:
            handle = token.store_handle
            if handle and not (handle.store is self and start <= handle.index <= end):
                raise ValueError('Token already in a store.')
        for token in self._tokens[start:end]:
            token.store_handle = None
        for token in tokens:
            token.store_handle = _Handle(store=self, index=0, position=Position(0, 0, 0))
        self._tokens[start:end] = tokens
        self._update_token_handles(start)

    def splice(self, tokens: Collection[_T], ref: Optional[_T], del_end: Optional[_T] = None) -> None:
        start = _check_store_handle(ref).index if ref else 0
        end = _check_store_handle(del_end).index + 1 if del_end else start
        self._splice(tokens, start, end)

    def insert_after(self, ref: Optional[_T], tokens: Collection[_T]) -> None:
        if ref is None:
            start = 0
        else:
            start = _check_store_handle(ref).index + 1
        self._splice(tokens, start, start)

    def insert_before(self, ref: Optional[_T], tokens: Collection[_T]) -> None:
        self.splice(tokens, ref)

    def update(self, token: _T) -> None:
        handle = _check_store_handle(token)
        self._update_token_handles(handle.index + 1)

    def replace(self, token: _T, repl: _T) -> None:
        self.splice([repl], token, token)

    def remove(self, start: _T, end: Optional[_T] = None) -> None:
        self.splice([], start, end or start)

    def iter(self, start: _T, end: _T) -> Iterator[_T]:
        start_idx = _check_store_handle(start).index
        end_idx = _check_store_handle(end).index
        yield from self._tokens[start_idx:end_idx + 1]

    def get_index(self, token: _T) -> int:
        handle = _check_store_handle(token)
        return handle.index

    def get_position(self, token: _T) -> Position:
        handle = _check_store_handle(token)
        return handle.position

    def get_by_position(self, position: int) -> _T:
        index = bisect.bisect_left(
            self._tokens, position, key=lambda t: _check_store_handle(t).position.position)
        token = next((token for token in self._tokens[index:] if token.raw_text), None)
        if token is None or _check_store_handle(token).position.position != position:
            raise KeyError(f'No token found at position {position}.')
        return token

    def find_by_line(self, line: int) -> Iterator[_T]:  # zero-based
        index = bisect.bisect_left(
            self._tokens, line, key=lambda t: _check_store_handle(t).position.line)
        while index < len(self._tokens):
            token = self._tokens[index]
            if not token.raw_text:
                continue
            if _check_store_handle(token).position.line >= line:
                break
            yield self._tokens[index]

    def get_prev(self, token: _T) -> Optional[_T]:
        index = _check_store_handle(token).index
        return self._tokens[index - 1] if index else None

    def get_next(self, token: _T) -> Optional[_T]:
        index = _check_store_handle(token).index
        return self._tokens[index + 1] if index + 1 < len(self._tokens) else None

    def get_first(self) -> Optional[_T]:
        return next(iter(self._tokens), None)

    def get_last(self) -> Optional[_T]:
        return next(reversed(self._tokens), None)

    def __iter__(self) -> Iterator[_T]:
        yield from self._tokens

    def __len__(self) -> int:
        return len(self._tokens)

    @ property
    def size(self) -> int:
        return self._end.position
