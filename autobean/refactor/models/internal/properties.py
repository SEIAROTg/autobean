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

    def _tokens_to_insert(self, values: list[_M]) -> list[base.RawTokenModel]:
        return list(itertools.chain.from_iterable([
            *copy.deepcopy(self._field.separators),
            *value.detach(),
        ] for value in values))

    def _prev_last(self, index: int) -> base.RawTokenModel:
        return (self._repeated.items[index - 1].last_token
            if index > 0 else self._repeated.placeholder)

    def _del_tokens(self, start: int, stop: int) -> None:
        if stop <= start:
            return
        prev_last = self._prev_last(start)
        first_token = self._repeated.token_store.get_next(prev_last)
        assert first_token is not None
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
            self._repeated.token_store.insert_after(
                self._prev_last(r.start),
                self._tokens_to_insert(values))
            self._repeated.items[indexes.slice_from_range(r)] = values
        else:
            if len(r) != len(values):
                raise ValueError(f'attempt to assign sequence of size {len(values)} to extended slice of size {len(r)}')
            for i, value in zip(r, values):
                self._del_tokens(i, i + 1)
                self._repeated.token_store.insert_after(
                    self._prev_last(i),
                    self._tokens_to_insert([value]))
                self._repeated.items[i] = value

    def insert(self, index: int, value: _M) -> None:
        index = min(index, len(self._repeated.items))
        self._repeated.token_store.insert_after(
            self._prev_last(index),
            self._tokens_to_insert([value]))
        self._repeated.items.insert(index, value)

    def append(self, value: _M) -> None:
        self._repeated.token_store.insert_after(
            self._repeated.last_token,
            self._tokens_to_insert([value]))
        value.reattach(self._repeated.token_store)
        self._repeated.items.append(value)

    def clear(self) -> None:
        self._del_tokens(0, len(self._repeated.items))
        self._repeated.items.clear()

    def extend(self, values: Iterable[_M]) -> None:
        values = list(values)
        self._repeated.token_store.insert_after(
            self._repeated.last_token,
            self._tokens_to_insert(values))
        self._repeated.items.extend(values)

    def pop(self, index: int = -1) -> _M:
        value = self._repeated.items.pop(index)
        tokens = value.tokens
        self._repeated.token_store.remove(value.first_token, value.last_token)
        token_store = base.TokenStore.from_tokens(tokens)
        value.reattach(token_store)
        return value

    def __deepcopy__(self, memo: dict[int, Any]) -> 'RepeatedNodeWrapper':
        repeated = copy.deepcopy(self._repeated, memo)
        return RepeatedNodeWrapper(repeated, self._field)

    def drop_many(self, indexes: Iterable[int]) -> None:
        indexes = set(indexes)
        for index in sorted(indexes, reverse=True):
            self._del_tokens(index, index + 1)
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
