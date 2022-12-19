import dataclasses
import decimal
import inspect
import types
from typing import Any, ClassVar, NewType, Type, TypeVar, Union, get_args, get_origin
import beancount.core.account
from beancount.core.data import Custom, Directive
from beancount.core.amount import Amount
from beancount.parser import grammar
from autobean.utils import error_lib

_T = TypeVar('_T')
_C = TypeVar('_C', bound='TypedCustom')


@dataclasses.dataclass(frozen=True)
class Account:
    name: str


@dataclasses.dataclass(frozen=True)
class Currency:
    name: str


@dataclasses.dataclass(frozen=True)
class TypedCustom:
    TYPE: ClassVar[str] = ''
    ERROR_MESSAGE: ClassVar[str] = ''
    custom: Custom

    @classmethod
    def try_parse(cls: Type[_C], directive: Directive) -> _C | error_lib.Error | None:
        if not isinstance(directive, Custom) or directive.type != cls.TYPE:
            return None
        arg_stream = _ArgumentStream(directive.values)
        args = []
        try:
            for arg_type in inspect.get_annotations(cls).values():
                if get_origin(arg_type) is list:
                    inner_type, = get_args(arg_type)
                    args.append(arg_stream.take_all(inner_type))
                else:
                    args.append(arg_stream.take_one(arg_type))
            if arg_stream.has_next():
                raise ValueError()
        except (IndexError, ValueError):
            return error_lib.InvalidDirectiveError(
                directive.meta, cls.ERROR_MESSAGE, directive)
        return cls(directive, *args)


class _ArgumentStream:
    def __init__(self, values: list[grammar.ValueType]):
        self._queue = (values or [])[::-1]

    def _next(self) -> Any:
        return self._queue.pop()

    def has_next(self) -> bool:
        return bool(self._queue)

    def take_one(self, arg_type: Type[_T]) -> _T:
        value = self._next()
        if get_origin(arg_type) is types.UnionType:
            options = get_args(arg_type)
        else:
            options = (arg_type,)
        for option in options:
            if option is Account:
                if value.dtype == beancount.core.account.TYPE:
                    return Account(value.value)  # type: ignore[return-value]
            elif option is decimal.Decimal and value.dtype is Amount:
                if value.value.number is not None:
                    self._queue.append(grammar.ValueType(Currency(value.value.currency), Currency))
                    return value.value.number
            else:
                if value.dtype is option:
                    return value.value
        raise ValueError()

    def take_all(self, arg_type: Type[_T]) -> list[_T]:
        rets = []
        while self.has_next():
            rets.append(self.take_one(arg_type))
        return rets
