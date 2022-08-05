import copy
import itertools
from typing import Any, Callable, Collection, Iterable, MutableSequence, Optional, Sequence, TypeVar, overload
from .base_property import base_property
from .fields import required_field, optional_field, repeated_field
from .maybe import Maybe
from .repeated import Repeated
from .base_property import base_property
from . import indexes
from .. import base

_M = TypeVar('_M', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)


def _replace_node(node: _M, repl: _M) -> None:
    token_store = node.token_store  # backup because the RawTokenModel.token_store may disappear
    if not token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    token_store.splice(repl.detach(), node.first_token, node.last_token)
    if isinstance(repl, base.RawTreeModel):
        repl.reattach(token_store)


class required_node_property(base_property[_M, base.RawTreeModel]):
    def __init__(self, inner_field: required_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field

    def _get(self, instance: base.RawTreeModel) -> _M:
        return self._inner_field.__get__(instance)

    def __set__(self, instance: base.RawTreeModel, value: _M) -> None:
        assert value is not None
        current = self._inner_field.__get__(instance)
        _replace_node(current, value)
        self._inner_field.__set__(instance, value)


class optional_node_property(base_property[Optional[_M], base.RawTreeModel]):
    def __init__(self, inner_field: optional_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field
        self._fcreator: Optional[Callable[[_U, Maybe[_M], _M], None]] = None
        self._fremover: Optional[Callable[[_U, Maybe[_M], _M], None]] = None

    def _get(self, instance: _U) -> Optional[_M]:
        return self._inner_field.__get__(instance).inner

    def __set__(self, instance: _U, inner: Optional[_M]) -> None:
        maybe = self._inner_field.__get__(instance)
        if maybe.inner is None and inner is not None:
            self._fcreator(instance, maybe, inner) if self._fcreator else maybe.create_inner(inner, separators=self._inner_field.separators)
        elif maybe.inner is not None and inner is None:
            self._fremover(instance, maybe, maybe.inner) if self._fremover else maybe.remove_inner(maybe.inner)
        elif maybe.inner is not None and inner is not None:
            _replace_node(maybe.inner, inner)
        maybe.inner = inner

    def creator(self, fcreator: Callable[[_U, Maybe[_M], _M], None]) -> None:
        self._fcreator = fcreator

    def remover(self, fremover: Callable[[_U, Maybe[_M], _M], None]) -> None:
        self._fremover = fremover


class RepeatedNodeWrapper(MutableSequence[_M]):
    def __init__(self, repeated: Repeated[_M], field: repeated_field) -> None:
        self._repeated = repeated
        self._field = field

    @property
    def repeated(self) -> Repeated[_M]:
        return self._repeated

    def __len__(self) -> int:
        return len(self._repeated.items)

    @overload
    def __getitem__(self, index: int) -> _M:
        ...
    @overload
    def __getitem__(self, index: slice) -> list[_M]:
        ...
    def __getitem__(self, index: int | slice) -> _M | list[_M]:
        return self._repeated.items[index]

    def __delitem__(self, index: int | slice) -> None:
        r = indexes.range_from_index(index, len(self._repeated.items))
        if r.step == 1:
            self[indexes.slice_from_range(r)] = []
        else:
            self.drop_many(r)

    def _insert_tokens(self, index: int, values: Iterable[base.RawModel]) -> None:
        tokens: list[base.RawTokenModel] = []
        ref = self._prev_last(index)
        for i, value in enumerate(values):
            if i or index or self._field.separators_before is None:
                tokens.extend(copy.deepcopy(self._field.separators))
                tokens.extend(value.detach())
            elif len(self._repeated.items):
                tokens.extend(value.detach())
                tokens.extend(copy.deepcopy(self._field.separators))
                t = self._repeated.token_store.get_prev(self._repeated.items[0].first_token)
                assert t is not None
                ref = t
            else:
                tokens.extend(copy.deepcopy(self._field.separators_before))
                tokens.extend(value.detach())
        self._repeated.token_store.insert_after(ref, tokens)

    def _prev_last(self, index: int) -> base.RawTokenModel:
        return (self._repeated.items[index - 1].last_token
            if index > 0 else self._repeated.placeholder)

    def _del_tokens(self, start: int, stop: int) -> None:
        # Consecutive tokens must be deleted in the same call.
        if stop <= start:
            return
        if start == 0 and stop < len(self._repeated.items) and self._field.separators_before is not None:
            first_token = self._repeated.items[start].first_token
            next_first = self._repeated.items[stop].first_token
            t = self._repeated.token_store.get_prev(next_first)
            assert t is not None
            last_token = t
        else:
            prev_last = self._prev_last(start)
            t = self._repeated.token_store.get_next(prev_last)
            assert t is not None
            first_token = t
            last_token = self._repeated.items[stop - 1].last_token
        self._repeated.token_store.remove(first_token, last_token)

    @overload
    def __setitem__(self, index: int, value: _M) -> None:
        ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[_M]) -> None:
        ...
    def __setitem__(self, index: int | slice, value: _M | Iterable[_M]) -> None:
        if isinstance(index, int):
            assert not isinstance(value, Iterable)
            values = [value]
        else:
            assert isinstance(value, Iterable)
            values = list(value)
        r = indexes.range_from_index(index, len(self._repeated.items))
        if r.step == 1:
            self._del_tokens(r.start, r.stop)
            self._insert_tokens(r.start, values)
            self._repeated.items[indexes.slice_from_range(r)] = values
        else:
            if len(r) != len(values):
                raise ValueError(f'attempt to assign sequence of size {len(values)} to extended slice of size {len(r)}')
            for i, value in zip(r, values):
                self._del_tokens(i, i + 1)
                self._insert_tokens(i, [value])
                self._repeated.items[i] = value

    def insert(self, index: int, value: _M) -> None:
        index = min(index, len(self._repeated.items))
        self._insert_tokens(index, [value])
        self._repeated.items.insert(index, value)

    def append(self, value: _M) -> None:
        self._insert_tokens(len(self._repeated.items), [value])
        value.reattach(self._repeated.token_store)
        self._repeated.items.append(value)

    def clear(self) -> None:
        self._del_tokens(0, len(self._repeated.items))
        self._repeated.items.clear()

    def extend(self, values: Iterable[_M]) -> None:
        values = list(values)
        self._insert_tokens(len(self._repeated.items), values)
        self._repeated.items.extend(values)

    def pop(self, index: int = -1) -> _M:
        value = self._repeated.items[index]
        tokens = value.tokens
        r = indexes.range_from_index(index, len(self._repeated.items))
        self._del_tokens(r.start, r.stop)
        token_store = base.TokenStore.from_tokens(tokens)
        value.reattach(token_store)
        self._repeated.items.pop(index)
        return value

    def __deepcopy__(self, memo: dict[int, Any]) -> 'RepeatedNodeWrapper':
        repeated = copy.deepcopy(self._repeated, memo)
        return RepeatedNodeWrapper(repeated, self._field)

    def drop_many(self, indexes: Iterable[int]) -> None:
        indexes = sorted(indexes, reverse=True)
        count = itertools.count()
        ranges = (
            list(r) for _, r in itertools.groupby(indexes, key=lambda i: i + next(count))
        )
        for r in ranges:
            self._del_tokens(r[-1], r[0] + 1)
        self._repeated.items[:] = (
            item for i, item in enumerate(self._repeated.items) if i not in indexes
        )

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Collection) and
            all(a == b for a, b in itertools.zip_longest(self, other)))


class repeated_node_property(base_property[RepeatedNodeWrapper[_M], base.RawTreeModel]):
    def __init__(self, inner_field: repeated_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field

    def __set_name__(self, owner: base.RawTreeModel, name: str) -> None:
        self._attr = name

    def _get(self, instance: _U) -> RepeatedNodeWrapper[_M]:
        wrapper = instance.__dict__.get(self._attr)
        if wrapper is None:
            repeated = self._inner_field.__get__(instance)
            wrapper = RepeatedNodeWrapper(repeated, self._inner_field)
            instance.__dict__[self._attr] = wrapper
        return wrapper

    def __set__(self, instance: _U, value: RepeatedNodeWrapper[_M]) -> None:
        repeated = self._inner_field.__get__(instance)
        _replace_node(repeated, value.repeated)
        self._inner_field.__set__(instance, value.repeated)
        instance.__dict__[self._attr] = value
