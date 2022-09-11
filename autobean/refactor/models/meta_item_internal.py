from typing import Generic, ItemsView, Iterable, Iterator, KeysView, Mapping, MutableMapping, Optional, Type, TypeVar, ValuesView, no_type_check, overload
from .meta_item import MetaItem
from .meta_value import MetaRawValue, MetaValue
from . import base, internal

_V = TypeVar('_V')


class _Empty:
    pass


_EMPTY = _Empty()


class _DictView:
    def __init__(self, wrapper: internal.RepeatedValueWrapper[MetaItem, MetaItem]):
        self._wrapper = wrapper

    def __len__(self) -> int:
        return len(self._wrapper)


class RepeatedRawMetaKeysView(_DictView, KeysView[str]):
    def __iter__(self) -> Iterator[str]:
        for item in self._wrapper:
            yield item.key

    def __reversed__(self) -> Iterator[str]:
        for item in reversed(self._wrapper):
            yield item.key


class RepeatedRawMetaValuesView(_DictView, ValuesView[MetaItem]):
    def __iter__(self) -> Iterator[MetaItem]:
        return iter(self._wrapper)

    def __reversed__(self) -> Iterator[MetaItem]:
        return reversed(self._wrapper)


class RepeatedRawMetaItemsView(_DictView, ItemsView[str, MetaItem]):
    def __iter__(self) -> Iterator[tuple[str, MetaItem]]:
        for item in self._wrapper:
            yield item.key, item

    def __reversed__(self) -> Iterator[tuple[str, MetaItem]]:
        for item in reversed(self._wrapper):
            yield item.key, item


class RepeatedRawMetaItemWrapper(
        internal.RepeatedFilteredNodeWrapper[MetaItem],
        MutableMapping[str, MetaItem]):

    def __init__(
            self,
            raw_wrapper: internal.RepeatedNodeWithInterleavingCommentsWrapper[MetaItem],
    ) -> None:
        super().__init__(raw_wrapper, MetaItem)

    @overload
    def __getitem__(self, index: int) -> MetaItem:
        ...
    @overload
    def __getitem__(self, index: slice) -> list[MetaItem]:
        ...
    @overload
    def __getitem__(self, index: str) -> MetaItem:
        ...
    def __getitem__(self, index: int | slice | str) -> MetaItem | list[MetaItem] | MetaItem:
        if not isinstance(index, str):
            return super().__getitem__(index)
        for item in self:
            if item.key == index:
                return item
        raise KeyError(index)

    def __delitem__(self, index: int | slice | str) -> None:
        if not isinstance(index, str):
            return super().__delitem__(index)
        for i, item in enumerate(self):
            if item.key == index:
                return super().__delitem__(i)
        raise KeyError(index)

    @overload
    def __setitem__(self, index: int, value: MetaItem) -> None:
        ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[MetaItem]) -> None:
        ...
    @overload
    def __setitem__(self, index: str, value: MetaItem) -> None:
        ...
    @no_type_check  # mypy does not seem to work well with overload
    def __setitem__(self, index: int | slice | str, value: MetaItem | Iterable[MetaItem]) -> None:
        if not isinstance(index, str):
            return super().__setitem__(index, value)
        for i, item in enumerate(self):
            if item.key == index:
                return super().__setitem__(i, value)
        self.append(value)

    @overload
    def pop(self, index: int = -1) -> MetaItem:
        ...
    @overload
    def pop(self, index: str) -> MetaItem:
        ...
    @overload
    def pop(self, index: str, default: _V) -> MetaItem | _V:
        ...
    def pop(self, index: int | str = -1, default: _V | _Empty = _EMPTY) -> MetaItem | _V:
        if not isinstance(index, str):
            return super().pop(index)
        for i, item in enumerate(self):
            if item.key == index:
                return super().pop(i)
        if not isinstance(default, _Empty):
            return default
        raise KeyError(index)

    def keys(self) -> KeysView[str]:
        return RepeatedRawMetaKeysView(self)

    def values(self) -> ValuesView[MetaItem]:
        return RepeatedRawMetaValuesView(self)

    def items(self) -> ItemsView[str, MetaItem]:
        return RepeatedRawMetaItemsView(self)


class RepeatedMetaKeysView(_DictView, KeysView[str]):
    def __iter__(self) -> Iterator[str]:
        for item in self._wrapper:
            yield item.key

    def __reversed__(self) -> Iterator[str]:
        for item in reversed(self._wrapper):
            yield item.key


class RepeatedMetaValuesView(_DictView, ValuesView[Optional[MetaValue]]):
    def __iter__(self) -> Iterator[Optional[MetaValue]]:
        for item in self._wrapper:
            yield item.value

    def __reversed__(self) -> Iterator[Optional[MetaValue]]:
        for item in reversed(self._wrapper):
            yield item.value


class RepeatedMetaItemsView(_DictView, ItemsView[str, Optional[MetaValue]]):
    def __iter__(self) -> Iterator[tuple[str, Optional[MetaValue]]]:
        for item in self._wrapper:
            yield item.key, item.value

    def __reversed__(self) -> Iterator[tuple[str, Optional[MetaValue]]]:
        for item in reversed(self._wrapper):
            yield item.key, item.value


class RepeatedMetaItemWrapper(
        internal.RepeatedFilteredNodeWrapper[MetaItem],
        MutableMapping[str, Optional[MetaValue | MetaRawValue]]):

    def __init__(
            self,
            raw_wrapper: internal.RepeatedNodeWithInterleavingCommentsWrapper[MetaItem],
    ) -> None:
        super().__init__(raw_wrapper, MetaItem)

    @overload
    def __getitem__(self, index: int) -> MetaItem:
        ...
    @overload
    def __getitem__(self, index: slice) -> list[MetaItem]:
        ...
    @overload
    def __getitem__(self, index: str) -> Optional[MetaValue]:
        ...
    def __getitem__(self, index: int | slice | str) -> MetaItem | list[MetaItem] | Optional[MetaValue]:
        if not isinstance(index, str):
            return super().__getitem__(index)
        for item in self:
            if item.key == index:
                return item.value
        raise KeyError(index)

    def __delitem__(self, index: int | slice | str) -> None:
        if not isinstance(index, str):
            return super().__delitem__(index)
        for i, item in enumerate(self):
            if item.key == index:
                return super().__delitem__(i)
        raise KeyError(index)

    @overload
    def __setitem__(self, index: int, value: MetaItem) -> None:
        ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[MetaItem]) -> None:
        ...
    @overload
    def __setitem__(self, index: str, value: Optional[MetaValue | MetaRawValue]) -> None:
        ...
    @no_type_check  # mypy does not seem to work well with overload
    def __setitem__(self, index: int | slice | str, value: MetaItem | Iterable[MetaItem] | Optional[MetaValue | MetaRawValue]) -> None:
        if not isinstance(index, str):
            return super().__setitem__(index, value)
        for _, item in enumerate(self):
            if item.key == index:
                item.value = value
                return
        self.append(MetaItem.from_value(index, value, indent=self.indent))

    @overload
    def pop(self, index: int = -1) -> MetaItem:
        ...
    @overload
    def pop(self, index: str) -> Optional[MetaValue]:
        ...
    @overload
    def pop(self, index: str, default: _V) -> Optional[MetaValue] | _V:
        ...
    def pop(self, index: int | str = -1, default: _V | _Empty = _EMPTY) -> MetaItem | Optional[MetaValue] | _V:
        if not isinstance(index, str):
            return super().pop(index)
        for i, item in enumerate(self):
            if item.key != index:
                continue
            item = super().pop(i)
            value = item.value
            if isinstance(value, base.RawModel) and value.token_store:
                if prev := value.token_store.get_prev(value.first_token):
                    value.token_store.remove(item.first_token, prev)
                if next := value.token_store.get_next(value.last_token):
                    value.token_store.remove(next, item.last_token)
            return value
        if not isinstance(default, _Empty):
            return default
        raise KeyError(index)

    def keys(self) -> KeysView[str]:
        return RepeatedMetaKeysView(self)

    def values(self) -> ValuesView[Optional[MetaValue]]:
        return RepeatedMetaValuesView(self)

    def items(self) -> ItemsView[str, Optional[MetaValue]]:
        return RepeatedMetaItemsView(self)


class repeated_raw_meta_item_property(internal.cached_custom_property[RepeatedRawMetaItemWrapper, base.RawTreeModel]):
    def __init__(self, inner_property: internal.repeated_node_with_interleaving_comments_property[MetaItem]):
        super().__init__(
            lambda instance: RepeatedRawMetaItemWrapper(inner_property.__get__(instance)))


class repeated_meta_item_property(internal.cached_custom_property[RepeatedMetaItemWrapper, base.RawTreeModel]):
    def __init__(self, inner_property: internal.repeated_node_with_interleaving_comments_property[MetaItem]):
        super().__init__(
            lambda instance: RepeatedMetaItemWrapper(inner_property.__get__(instance)))


def from_mapping(mapping: Mapping[str, MetaValue | MetaRawValue]) -> Iterator[MetaItem]:
    for key, value in mapping.items():
        yield MetaItem.from_value(key, value)
