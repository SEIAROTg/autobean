import abc
import copy
import functools
import itertools
from typing import Any, Callable, Collection, Iterable, MutableSequence, Optional, Type, TypeVar, overload
from .base_property import base_ro_property, base_rw_property
from .fields import required_field, optional_field, repeated_field
from .repeated import Repeated
from . import indexes
from .. import base

_M = TypeVar('_M', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)
_V = TypeVar('_V')


def replace_node(node: _M, repl: _M) -> None:
    token_store = node.token_store  # backup because the RawTokenModel.token_store may disappear
    if not token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    token_store.splice(repl.detach(), node.first_token, node.last_token)
    if isinstance(repl, base.RawTreeModel):
        repl.reattach(token_store)


class required_node_property(base_rw_property[_M, base.RawTreeModel]):
    def __init__(self, inner_field: required_field[_M]) -> None:
        super().__init__()
        self._inner_field = inner_field

    def _get(self, instance: base.RawTreeModel) -> _M:
        return self._inner_field.__get__(instance)

    def __set__(self, instance: base.RawTreeModel, value: _M) -> None:
        assert value is not None
        current = self._inner_field.__get__(instance)
        replace_node(current, value)
        self._inner_field.__set__(instance, value)


class optional_node_property(base_rw_property[Optional[_M], _U]):
    def __init__(
            self,
            inner_field: optional_field[_M],
            pivot_property: base_ro_property[base.RawTokenModel, _U],
    ) -> None:
        super().__init__()
        self._inner_field = inner_field
        self._pivot_property = pivot_property

    def _get(self, instance: _U) -> Optional[_M]:
        return self._inner_field.__get__(instance)

    def __set__(self, instance: _U, value: Optional[_M]) -> None:
        current = self._inner_field.__get__(instance)
        if current is None and value is not None:
            pivot = self._pivot_property.__get__(instance)
            self._inner_field._create_node(instance.token_store, pivot, value)
        elif current is not None and value is None:
            pivot = self._pivot_property.__get__(instance)
            self._inner_field._remove_node(instance.token_store, pivot, current)
        elif current is not None and value is not None:
            replace_node(current, value)
        self._inner_field.__set__(instance, value)


class RepeatedNodeWrapper(MutableSequence[_M]):
    def __init__(self, repeated: Repeated[_M], field: repeated_field) -> None:
        self._repeated = repeated
        self._field = field

    @property
    def repeated(self) -> Repeated[_M]:
        return self._repeated

    @functools.cached_property
    def indent(self) -> Optional[str]:
        if self._field.default_indent is None:
            return None
        elif self._repeated.inferred_indent is not None:
            return self._repeated.inferred_indent
        else:
            return self._field.default_indent

    @functools.cached_property
    def _separators(self) -> tuple[base.RawTokenModel, ...]:
        return self._field.separators

    @functools.cached_property
    def _separators_before(self) -> tuple[base.RawTokenModel, ...]:
        return (
            self._field.separators_before
            if self._field.separators_before is not None else self._field.separators)

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

    def _insert_tokens(
            self,
            index: int,
            values: Iterable[base.RawModel],
            length: Optional[int] = None,
            separators_before_last: Optional[base.RawTokenModel] = None,
    ) -> None:
        tokens: list[base.RawTokenModel] = []
        ref = self._prev_last(index)
        if length is None:
            length = len(self._repeated.items)
        for i, value in enumerate(values):
            if i or index:
                tokens.extend(copy.deepcopy(self._separators))
                tokens.extend(value.detach())
            elif length:
                tokens.extend(value.detach())
                tokens.extend(copy.deepcopy(self._separators))
                if separators_before_last is None:
                    separators_before_last = self._repeated.token_store.get_prev(
                        self._repeated.items[0].first_token)
                    assert separators_before_last is not None
                ref = separators_before_last
            else:
                tokens.extend(copy.deepcopy(self._separators_before))
                tokens.extend(value.detach())
        self._repeated.token_store.insert_after(ref, tokens)

    def _prev_last(self, index: int) -> base.RawTokenModel:
        return (self._repeated.items[index - 1].last_token
            if index > 0 else self._repeated.placeholder)

    def _del_tokens(self, start: int, stop: int) -> None:
        # Consecutive tokens must be deleted in the same call.
        if stop <= start:
            return
        if start == 0 and stop < len(self._repeated.items):
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
            item = self._repeated.items[index]
            self._repeated.token_store.splice(value.detach(), item.first_token, item.last_token)
            value.reattach(self._repeated.token_store)
            self._repeated.items[index] = value
            return
        assert isinstance(value, Iterable)
        values = list(value)
        r = indexes.range_from_index(index, len(self._repeated.items))
        separators_before_last = (
            self._repeated.token_store.get_prev(self._repeated.items[0].first_token)
            if self._repeated.items else None)
        if r.step == 1:
            self._del_tokens(r.start, r.stop)
            self._insert_tokens(
                r.start, values, len(self._repeated.items) - len(r), separators_before_last)
            self._repeated.items[indexes.slice_from_range(r)] = values
        else:
            if len(r) != len(values):
                raise ValueError(f'attempt to assign sequence of size {len(values)} to extended slice of size {len(r)}')
            for i, value in zip(r, values):
                self._del_tokens(i, i + 1)
                self._insert_tokens(i, [value], len(self._repeated.items) - 1, separators_before_last)
                value.reattach(self._repeated.token_store)
                self._repeated.items[i] = value

    def insert(self, index: int, value: _M) -> None:
        index = min(index, len(self._repeated.items))
        self._insert_tokens(index, [value])
        value.reattach(self._repeated.token_store)
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

    def auto_claim_comments(self) -> None:
        self._repeated.auto_claim_comments()


class repeated_node_property(base_rw_property[RepeatedNodeWrapper[_M], base.RawTreeModel]):
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
        replace_node(repeated, value.repeated)
        self._inner_field.__set__(instance, value.repeated)
        instance.__dict__[self._attr] = value


def _default_fset(instance: _U, value: _V) -> None:
    raise NotImplementedError()


class custom_property(base_rw_property[_V, _U]):
    def __init__(self, fget: Callable[[_U], _V]) -> None:
        super().__init__()
        self._fget = fget
        self._fset: Callable[[_U, _V], None] = _default_fset

    def setter(self, fset: Callable[[_U, _V], None]) -> 'custom_property[_V, _U]':
        self._fset = fset
        return self

    def _get(self, instance: _U) -> _V:
        return self._fget(instance)

    def __set__(self, instance: _U, value: _V) -> None:
        self._fset(instance, value)


class cached_custom_property(custom_property[_V, _U]):
    def __set_name__(self, owner: _U, name: str) -> None:
        self._attr = name

    def _get(self, instance: _U) -> _V:
        if self._attr in instance.__dict__:
            return instance.__dict__[self._attr]
        value = self._fget(instance)
        instance.__dict__[self._attr] = value
        return value

    def __set__(self, instance: _U, value: _V) -> None:
        super().__set__(instance, value)
        instance.__dict__[self._attr] = value


class unordered_node_property(base_rw_property[Optional[_V], _U]):
    def __init__(
            self,
            inner_property: base_rw_property[MutableSequence[_V | _M], _U],
            inner_type: Type[_V],
            *,
            prepend: bool = False,
    ) -> None:
        super().__init__()
        self._inner_property = inner_property
        self._inner_type = inner_type
        self._prepend = prepend

    def _get(self, instance: _U) -> Optional[_V]:
        wrapper = self._inner_property.__get__(instance)
        return next((item for item in wrapper if isinstance(item, self._inner_type)), None)

    def __set__(self, instance: _U, value: Optional[_V]) -> None:
        wrapper = self._inner_property.__get__(instance)
        i = next((i for i, item in enumerate(wrapper) if isinstance(item, self._inner_type)), None)
        if i is None and value is not None:
            if self._prepend:
                wrapper.insert(0, value)
            else:
                wrapper.append(value)
        elif i is not None and value is None:
            wrapper.pop(i)
        elif i is not None and value is not None:
            wrapper[i] = value
