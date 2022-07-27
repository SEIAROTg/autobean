import abc
import copy
import enum
from typing import Callable, Generic, Type, TypeVar, Optional, final, overload
from . import base
from . import placeholder

_TT = TypeVar('_TT', bound=Type[base.RawTokenModel])
_UT = TypeVar('_UT', bound=Type[base.RawTreeModel])
_U = TypeVar('_U', bound=base.RawTreeModel)
_M = TypeVar('_M', bound=base.RawModel)
# TODO: replace with PEP 673 Self once supported
_SelfBaseProperty = TypeVar('_SelfBaseProperty', bound='_base_property')
_SelfSimpleRawTokenModel = TypeVar('_SelfSimpleRawTokenModel', bound='SimpleRawTokenModel')
_SelfSingleValueRawTokenModel = TypeVar('_SelfSingleValueRawTokenModel', bound='SingleValueRawTokenModel')
_SelfSimpleDefaultRawTokenModel = TypeVar('_SelfSimpleDefaultRawTokenModel', bound='SimpleDefaultRawTokenModel')
_SelfMaybe = TypeVar('_SelfMaybe', bound='Maybe')
_SelfMaybeL = TypeVar('_SelfMaybeL', bound='MaybeL')
_SelfMaybeR = TypeVar('_SelfMaybeR', bound='MaybeR')
_B = TypeVar('_B')
_V = TypeVar('_V')
_S = TypeVar('_S', bound='SingleValueRawTokenModel')

TOKEN_MODELS: list[Type[base.RawTokenModel]] = []
TREE_MODELS: list[Type[base.RawTreeModel]] = []


def token_model(cls: _TT) -> _TT:
    TOKEN_MODELS.append(cls)
    return cls


def tree_model(cls: _UT) -> _UT:
    TREE_MODELS.append(cls)
    return cls


class _base_property(Generic[_B, _U], abc.ABC):
    @abc.abstractmethod
    def _get(self, instance: _U) -> _B:
        ...

    @overload
    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> _B:
        ...

    @overload
    def __get__(self: _SelfBaseProperty, instance: None, owner: Type[_U]) -> _SelfBaseProperty:
        ...

    def __get__(self: _SelfBaseProperty, instance: Optional[_U], owner: Optional[Type[_U]] = None) -> _B | _SelfBaseProperty:
        del owner
        if instance is None:
            return self
        return self._get(instance)


def _replace_node(node: _M, repl: _M) -> None:
    token_store = node.token_store  # backup because the RawTokenModel.token_store may disappear
    if not token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    token_store.splice(repl.detach(), node.first_token, node.last_token)
    if isinstance(repl, base.RawTreeModel):
        repl.reattach(token_store)


class Floating(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


class Maybe(base.RawTreeModel, Generic[_M]):
    def __init__(
            self,
            token_store: base.TokenStore,
            inner: Optional[_M],
            placeholder: placeholder.Placeholder,
    ) -> None:
        super().__init__(token_store)
        self.inner = inner
        self._placeholder = placeholder

    @property
    def placeholder(self) -> placeholder.Placeholder:
        return self._placeholder

    def clone(self: _SelfMaybe, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfMaybe:
        return type(self)(
            token_store,
            self.inner.clone(token_store, token_transformer) if self.inner is not None else None,
            self.placeholder.clone(token_store, token_transformer))

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        if self.inner is not None:
            self.inner = self.inner.reattach(token_store, token_transformer)
        self._placeholder = self._placeholder.reattach(token_store, token_transformer)

    @abc.abstractmethod
    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...]) -> None:
        ...

    @abc.abstractmethod
    def remove_inner(self, inner: _M) -> None:
        ...


class MaybeL(Maybe[_M]):
    @property
    def first_token(self) -> base.RawTokenModel:
        return self.placeholder

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.inner.last_token if self.inner is not None else self.placeholder

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, MaybeL) and self.inner == other.inner

    @classmethod
    def from_children(
            cls: Type[_SelfMaybeL],
            inner: Optional[_M],
            *,
            separators: tuple[base.RawTokenModel, ...],
    ) -> _SelfMaybeL:
        ph = placeholder.Placeholder.from_default()
        tokens = [ph, *copy.deepcopy(separators), *inner.detach()] if inner is not None else [ph]
        token_store = base.TokenStore.from_tokens(tokens)
        return cls(token_store, inner, ph)

    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...],) -> None:
        self.token_store.insert_after(self.placeholder, [
            *copy.deepcopy(separators),
            *inner.detach(),
        ])
        inner.reattach(self.token_store)

    def remove_inner(self, inner: _M) -> None:
        first = self.token_store.get_next(self.placeholder)
        assert first is not None
        self.token_store.remove(first, inner.last_token)


class MaybeR(Maybe[_M]):
    @property
    def first_token(self) -> base.RawTokenModel:
        return self.inner.first_token if self.inner is not None else self.placeholder

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.placeholder

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, MaybeR) and self.inner == other.inner

    @classmethod
    def from_children(
            cls: Type[_SelfMaybeR],
            inner: Optional[_M],
            *,
            separators: tuple[base.RawTokenModel, ...],
    ) -> _SelfMaybeR:
        placeholder = placeholder.Placeholder.from_default()
        tokens = [*inner.detach(), *copy.deepcopy(separators), placeholder] if inner is not None else [placeholder]
        token_store = base.TokenStore.from_tokens(tokens)
        return cls(token_store, inner, placeholder)

    def create_inner(self, inner: _M, *, separators: tuple[base.RawTokenModel, ...],) -> None:
        self.token_store.insert_before(self.placeholder, [
            *inner.detach(),
            *copy.deepcopy(separators),
        ])
        inner.reattach(self.token_store)

    def remove_inner(self, inner: _M) -> None:
        last = self.token_store.get_prev(self.placeholder)
        assert last is not None
        self.token_store.remove(inner.first_token, last)


class field(_base_property[_V, base.RawTreeModel]):
    def __set_name__(self, owner: Type[base.RawTreeModel], name: str) -> None:
        self._attr = '_' + name

    def _get(self, instance: base.RawTreeModel) -> _V:
        return getattr(instance, self._attr)

    def __set__(self, instance: base.RawTreeModel, value: _V) -> None:
        setattr(instance, self._attr, value)


class required_field(field[_M]):
    pass


class optional_field(field[Maybe[_M]]):
    def __init__(self, *, floating: Floating, separators: tuple[base.RawTokenModel, ...]) -> None:
        self._floating = floating
        self._separators = separators

    @property
    def floating(self) -> Floating:
        return self._floating

    @property
    def separators(self) -> tuple[base.RawTokenModel, ...]:
        return self._separators


class required_node_property(_base_property[_M, base.RawTreeModel]):
    def __init__(self, inner_field: required_field[_M]) -> None:
        self._inner_field = inner_field

    def _get(self, instance: base.RawTreeModel) -> _M:
        return self._inner_field.__get__(instance)

    def __set__(self, instance: base.RawTreeModel, value: _M) -> None:
        assert value is not None
        current = self._inner_field.__get__(instance)
        _replace_node(current, value)
        self._inner_field.__set__(instance, value)


class optional_node_property(_base_property[Optional[_M], base.RawTreeModel]):
    def __init__(self, inner_field: optional_field[_M]) -> None:
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


class SimpleRawTokenModel(base.RawTokenModel):
    @final
    def __init__(self, raw_text: str) -> None:
        super().__init__(raw_text)

    def _clone(self: _SelfSimpleRawTokenModel) -> _SelfSimpleRawTokenModel:
        return type(self)(self.raw_text)


class SingleValueRawTokenModel(base.RawTokenModel, Generic[_V]):
    @final
    def __init__(self, raw_text: str, value: _V) -> None:
        super().__init__(raw_text)
        self._value = value

    @classmethod
    def from_raw_text(cls: Type[_S], raw_text: str) -> _S:
        return cls(raw_text, cls._parse_value(raw_text))

    @classmethod
    def from_value(cls: Type[_S], value: _V) -> _S:
        return cls(cls._format_value(value), value)

    @property
    def raw_text(self) -> str:
        return super().raw_text

    @raw_text.setter
    def raw_text(self, raw_text: str) -> None:
        self._update_raw_text(raw_text)
        self._value = self._parse_value(raw_text)

    @property
    def value(self) -> _V:
        return self._value

    @value.setter
    def value(self, value: _V) -> None:
        self._value = value
        self._raw_text = self._format_value(value)

    @classmethod
    @abc.abstractmethod
    def _parse_value(cls, raw_text: str) -> _V:
        pass

    @classmethod
    @abc.abstractmethod
    def _format_value(cls, value: _V) -> str:
        pass

    def _clone(self: _SelfSingleValueRawTokenModel) -> _SelfSingleValueRawTokenModel:
        return type(self)(self.raw_text, self.value)


class SimpleSingleValueRawTokenModel(SingleValueRawTokenModel[str]):
    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        return raw_text

    @classmethod
    def _format_value(cls, value: str) -> str:
        return value


class SimpleDefaultRawTokenModel(SimpleRawTokenModel):
    # not using @classmethod here because it suppresses abstractmethod errors.
    @property
    @abc.abstractmethod
    def DEFAULT(self) -> str:
        ...

    @classmethod
    def from_default(cls: Type[_SelfSimpleDefaultRawTokenModel]) -> _SelfSimpleDefaultRawTokenModel:
        return cls.from_raw_text(cls.DEFAULT)  # type: ignore[arg-type]


def list_fields(cls: Type[base.RawTreeModel]) -> list[field]:
    for base_class in cls.mro():
        if issubclass(base_class, base.RawTreeModel):
            fields = [v for v in base_class.__dict__.values() if isinstance(v, field)]
            if fields:
                return fields
    return []
