import abc
from typing import Callable, Generic, Type, TypeVar, Optional, overload
from autobean.refactor import token_store as token_store_lib
from . import base

_T = TypeVar('_T', bound=base.RawTokenModel)
_U = TypeVar('_U', bound=base.RawTreeModel)
_Self = TypeVar('_Self', bound='_base_property')  # TODO: replace with PEP 673 Self once supported
_B = TypeVar('_B')
_V = TypeVar('_V')
_S = TypeVar('_S', bound='SingleValueRawTokenModel')


class _base_property(Generic[_B, _U], abc.ABC):
    @abc.abstractmethod
    def _get(self, instance: _U) -> _B:
        ...

    @overload
    def __get__(self, instance: _U, owner: Optional[Type[_U]] = None) -> _B:
        ...

    @overload
    def __get__(self: _Self, instance: None, owner: Type[_U]) -> _Self:
        ...

    def __get__(self: _Self, instance: Optional[_U], owner: Optional[Type[_U]] = None) -> _B | _Self:
        del owner
        if instance is None:
            return self
        return self._get(instance)


class required_token_property(_base_property[_T, _U]):
    def __init__(self, inner: Callable[[_U], _T]):
        self._attr = '_' + inner.__name__

    def _get(self, instance: _U) -> _T:
        value = getattr(instance, self._attr)
        assert value
        return value

    def __set__(self, instance: _U, value: _T) -> None:
        assert value
        if hasattr(instance, self._attr):
            current = self.__get__(instance)
            instance.token_store.replace(current, value)
        setattr(instance, self._attr, value)


class optional_token_property(_base_property[Optional[_T], _U]):
    def __init__(self, inner: Callable[[_U], Optional[_T]]):
        self._attr = '_' + inner.__name__
        self._fcreator = lambda s, _: None
        self._fremover = lambda s, _: None

    def _get(self, instance: _U) -> Optional[_T]:
        value = getattr(instance, self._attr)
        return value

    def __set__(self, instance: _U, value: Optional[_T]) -> None:
        if hasattr(instance, self._attr):
            current = self.__get__(instance)
            if current is None and value is not None:
                self._fcreator(instance, value)
            elif current is not None and value is None:
                self._fremover(instance, current)
            elif current is not None and value is not None:
                instance.token_store.replace(current, value)
        setattr(instance, self._attr, value)

    def remover(self, fremover: Callable[[_U, _T], None]) -> None:
        # second argument of fremover is for easier type checking
        self._fremover = fremover

    def creator(self, fcreator: Callable[[_U, _T], None]) -> None:
        self._fcreator = fcreator


def remove_with_left_whitespace(token_store: token_store_lib.TokenStore, model: base.RawModel) -> None:
    start = model.first_token
    if start:
        prev = token_store.get_prev(start)
        if isinstance(prev, base.Whitespace):
            start = prev
    end = model.last_token
    token_store.splice((), start, end)


class SingleValueRawTokenModel(base.RawTokenModel, Generic[_V]):
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


class SimpleSingleValueRawTokenModel(SingleValueRawTokenModel[str]):
    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        return raw_text

    @classmethod
    def _format_value(cls, value: str) -> str:
        return value
