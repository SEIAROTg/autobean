import collections
import dataclasses
import decimal
import inspect
import re
import shlex
from typing import Any, Callable, ClassVar, Iterable, Iterator, NewType, Optional, Type, TypeVar, Union, get_args, get_origin
from beancount.core.data import Custom, Directive
from beancount.core.amount import Amount
from beancount.core import account as beancount_account
from beancount.parser import grammar
from autobean.utils import error_lib

Account = NewType('Account', str)
Currency = NewType('Currency', str)
_HANDLER_METADATA_ATTR = '_autobean_handler_metadata'
_T = TypeVar('_T', bound=Directive)
_R = TypeVar('_R', bound=Iterable[Directive])
_Plugin = TypeVar('_Plugin', bound='BasePlugin')
_RegularHandlerImpl = Callable[[_Plugin, _T], _R]
_CustomHandlerImpl = Callable[..., _R]  # (self, custom, *args)


@dataclasses.dataclass(frozen=True)
class _RegularHandlerMetadata:
    directive_type: Type[Directive]


@dataclasses.dataclass(frozen=True)
class _CustomHandlerMetadata:
    custom_type: str
    params_description: str
    params: list[inspect.Parameter]


class BasePlugin:
    _NAME: ClassVar[str]
    _ARGUMENT_TYPE: ClassVar[Any]
    _CUSTOM_SCOPE: ClassVar[Optional[re.Pattern]]
    _REGULAR_HANDLERS: ClassVar[dict[int, _RegularHandlerImpl]]
    _CUSTOM_HANDLERS: ClassVar[dict[str, list[tuple[_CustomHandlerMetadata, _CustomHandlerImpl]]]]

    _error_logger: error_lib.ErrorLogger

    def __init__(self) -> None:
        self._error_logger = error_lib.ErrorLogger()

    @classmethod
    def plugin(
            cls,
            entries: list[Directive],
            options: dict[str, Any],
            arg: Optional[str] = None,
    ) -> tuple[list[Directive], list[error_lib.Error]]:
        if cls._ARGUMENT_TYPE is None and arg is not None:
            raise ValueError(f'{cls._NAME} does not accept an argument')
        elif cls._ARGUMENT_TYPE is not None and arg is None:
            raise ValueError(f'{cls._NAME} expects an argument')
        inst = cls()
        return list(inst.process(entries, options, arg)), inst._error_logger.errors

    def process(
            self,
            entries: list[Directive],
            options: dict[str, Any],
            arg: Optional[str],
    ) -> Iterable[Directive]:
        if not self._REGULAR_HANDLERS and not self._CUSTOM_HANDLERS:
            return
        self._options = options
        self._argument = arg
        for entry in entries:
            yield from self._process_entry(entry)

    def _process_entry(self, entry: Directive) -> Iterator[Directive]:
        if isinstance(entry, Custom) and (handlers := self._CUSTOM_HANDLERS.get(entry.type)):
            for metadata, func in handlers:
                if (args := _get_args(entry.values or [], metadata)) is not None:
                    yield from func(self, entry, *args)
                    return
            self._error_logger.log_error(
                error_lib.InvalidDirectiveError(
                    entry.meta,
                    f'Invalid arguments: {shlex.quote(entry.type)} expects {metadata.params_description}.',
                    entry))
            return
        if handler := self._REGULAR_HANDLERS.get(id(type(entry))):
            yield from handler(self, entry)
            return
        yield entry
        if isinstance(entry, Custom) and (
                self._CUSTOM_SCOPE is not None and self._CUSTOM_SCOPE.match(entry.type)):
            self._error_logger.log_error(
                error_lib.InvalidDirectiveError(
                    entry.meta, f'Unrecognized custom directive {shlex.quote(entry.type)}.', entry))
            return


def _get_args(
        values: list[grammar.ValueType],
        metadata: _CustomHandlerMetadata,
) -> Optional[list[Any]]:
    queue = values[::-1]
    args = []
    for param in metadata.params:
        if param.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.POSITIONAL_ONLY):
            if (arg := _get_arg(param.annotation, queue)) is not None:
                args.append(arg)
            else:
                return None
        elif param.kind is inspect.Parameter.VAR_POSITIONAL:
            while queue:
                if (arg := _get_arg(param.annotation, queue)) is not None:
                    args.append(arg)
                else:
                    return None
    if queue:
        return None
    return args


def _get_arg(annotation: Any, queue: list[grammar.ValueType]) -> Optional[Any]:
    if not queue:
        return None
    value = queue.pop()
    if get_origin(annotation) is Union:
        options = get_args(annotation)
    else:
        options = (annotation,)
    for option in options:
        if value.dtype is option:
            return value.value
        elif option is Account:
            if value.dtype == beancount_account.TYPE:
                return Account(value.value)
        elif option is decimal.Decimal and value.dtype is Amount:
            if value.value.number is not None:
                queue.append(grammar.ValueType(Currency(value.value.currency), Currency))
                return value.value.number
    return None


def plugin(
        name: str,
        *,
        param_type: Any = None,
        custom_scope: Optional[str] = None,
) -> Callable[[Type[_Plugin]], Type[_Plugin]]:
    def decorator(cls: Type[_Plugin]) -> Type[_Plugin]:
        cls._NAME = name
        cls._ARGUMENT_TYPE = param_type
        cls._CUSTOM_SCOPE = re.compile(custom_scope) if custom_scope is not None else None
        regular_handlers = {}
        custom_handlers = collections.defaultdict(list) 
        for _, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            metadata = getattr(func, _HANDLER_METADATA_ATTR, None)
            if isinstance(metadata, _RegularHandlerMetadata):
                regular_handlers[id(metadata.directive_type)] = func
            elif isinstance(metadata, _CustomHandlerMetadata):
                custom_handlers[metadata.custom_type].append((metadata, func))
        cls._REGULAR_HANDLERS = regular_handlers
        cls._CUSTOM_HANDLERS = custom_handlers
        return cls
    return decorator


def handle(
        directive_type: Type[_T],
) -> Callable[[_RegularHandlerImpl[_Plugin, _T, _R]], _RegularHandlerImpl[_Plugin, _T, _R]]:
    def decorator(func: _RegularHandlerImpl[_Plugin, _T, _R]) -> _RegularHandlerImpl[_Plugin, _T, _R]:
        setattr(func, _HANDLER_METADATA_ATTR, _RegularHandlerMetadata(directive_type))
        return func
    return decorator


def handle_custom(custom_type: str, params_description: str) -> Callable[[_CustomHandlerImpl], _CustomHandlerImpl]:
    def decorator(func: _CustomHandlerImpl) -> _CustomHandlerImpl:
        setattr(func, _HANDLER_METADATA_ATTR, _CustomHandlerMetadata(
            custom_type=custom_type,
            params_description=params_description,
            params=list(inspect.signature(func).parameters.values())[2:]))
        return func
    return decorator
