import abc
import enum
from typing import Callable, Generic, Type, TypeVar, Optional, Union, final, overload
from . import base

_TT = TypeVar('_TT', bound=Type[base.RawTokenModel])
_UT = TypeVar('_UT', bound=Type[base.RawTreeModel])
_U = TypeVar('_U', bound=base.RawTreeModel)
_TU = TypeVar('_TU', bound=Union[base.RawTokenModel, base.RawTreeModel])
# TODO: replace with PEP 673 Self once supported
_SelfBaseProperty = TypeVar('_SelfBaseProperty', bound='_base_property')
_SelfSimpleRawTokenModel = TypeVar('_SelfSimpleRawTokenModel', bound='SimpleRawTokenModel')
_SelfSingleValueRawTokenModel = TypeVar('_SelfSingleValueRawTokenModel', bound='SingleValueRawTokenModel')
_SelfSimpleDefaultRawTokenModel = TypeVar('_SelfSimpleDefaultRawTokenModel', bound='SimpleDefaultRawTokenModel')
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


def _replace_node(node: _TU, repl: _TU) -> None:
    token_store = node.token_store  # backup because the RawTokenModel.token_store may disappear
    if not token_store:
        raise ValueError('Cannot replace a free token.')
    if node is repl:
        return
    token_store.splice(repl.detach(), node.first_token, node.last_token)
    if isinstance(repl, base.RawTreeModel):
        repl.reattach(token_store)


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

    def reset(self, instance: _U, value: _TU) -> None:
        setattr(instance, self._attr, value)


def _default_fcreator(instance: _U, value: _TU) -> None:
    raise NotImplementedError('creator not implemented')


def _default_fremover(instance: _U, current: _TU) -> None:
    raise NotImplementedError('remover not implemented')


class Floating(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


class OptionalNodeProperty(_base_property[Optional[_TU], _U]):
    def __init__(self, floating: Floating, inner: Callable[[_U], Optional[_TU]]):
        self._floating = floating
        self._attr = '_' + inner.__name__
        self._fcreator: Callable[[_U, _TU], None] = _default_fcreator
        self._fremover: Callable[[_U, _TU], None] = _default_fremover

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

    def creator(self, fcreator: Callable[[_U, _TU], None]) -> None:
        self._fcreator = fcreator

    def remover(self, fremover: Callable[[_U, _TU], None]) -> None:
        self._fremover = fremover

    def reset(self, instance: _U, value: Optional[_TU]) -> None:
        setattr(instance, self._attr, value)


def optional_node_property(
        *,
        floating: Floating,
) -> Callable[[Callable[[_U], _TU]], OptionalNodeProperty[_TU, _U]]:
    def decorator(inner: Callable[[_U], _TU]) -> OptionalNodeProperty[_TU, _U]:
        return OptionalNodeProperty(floating, inner)
    return decorator
    

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
