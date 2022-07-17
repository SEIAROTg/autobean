import abc
from typing import Callable, Generic, Type, TypeVar, Optional, Union, overload
from . import base

_TT = TypeVar('_TT', bound=Type[base.RawTokenModel])
_UT = TypeVar('_UT', bound=Type[base.RawTreeModel])
_U = TypeVar('_U', bound=base.RawTreeModel)
_TU = TypeVar('_TU', bound=Union[base.RawTokenModel, base.RawTreeModel])
_Self = TypeVar('_Self', bound='_base_property')  # TODO: replace with PEP 673 Self once supported
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
    def __get__(self: _Self, instance: None, owner: Type[_U]) -> _Self:
        ...

    def __get__(self: _Self, instance: Optional[_U], owner: Optional[Type[_U]] = None) -> _B | _Self:
        del owner
        if instance is None:
            return self
        return self._get(instance)


def _destruct_tree_model(model: base.RawModel) -> list[base.RawTokenModel]:
    if model.token_store is None:
        assert isinstance(model, base.RawTokenModel)
        return [model]
    if (
            model.first_token is not model.token_store.get_first() or
            model.last_token is not model.token_store.get_last()):
        raise ValueError('Cannot reuse node. Consider making a copy.')
    if not model.first_token or not model.last_token:
        raise ValueError('Cannot destruct empty node.')
    tokens = list(model.token_store.iter(model.first_token, model.last_token))
    model.token_store.remove(model.first_token, model.last_token)
    return tokens


def _replace_node(node: _TU, repl: _TU) -> None:
    if not node.token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    tokens = _destruct_tree_model(repl)
    node.token_store.splice(tokens, node.first_token, node.last_token)


class required_node_property(_base_property[_TU, _U]):
    def __init__(self, inner: Callable[[_U], _TU]):
        self._attr = '_' + inner.__name__

    def _get(self, instance: _U) -> _TU:
        value = getattr(instance, self._attr)
        assert value
        return value

    def __set__(self, instance: _U, value: _TU) -> None:
        assert value
        if hasattr(instance, self._attr):
            current = self.__get__(instance)
            _replace_node(current, value)
        setattr(instance, self._attr, value)


class optional_node_property(_base_property[Optional[_TU], _U]):
    def __init__(self, inner: Callable[[_U], Optional[_TU]]):
        self._attr = '_' + inner.__name__
        self._fcreator = lambda s, _: None
        self._fremover = lambda s, _: None

    def _get(self, instance: _U) -> Optional[_TU]:
        value = getattr(instance, self._attr)
        return value

    def __set__(self, instance: _U, value: Optional[_TU]) -> None:
        if hasattr(instance, self._attr):
            current = self.__get__(instance)
            if current is None and value is not None:
                self._fcreator(instance, value)
            elif current is not None and value is None:
                self._fremover(instance, current)
            elif current is not None and value is not None:
                _replace_node(current, value)
        setattr(instance, self._attr, value)

    def remover(self, fremover: Callable[[_U, _TU], None]) -> None:
        # second argument of fremover is for easier type checking
        self._fremover = fremover

    def creator(self, fcreator: Callable[[_U, _TU], None]) -> None:
        self._fcreator = fcreator


class SimpleRawTokenModel(base.RawTokenModel):
    def __init__(self, raw_text: str) -> None:
        super().__init__(raw_text)


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
