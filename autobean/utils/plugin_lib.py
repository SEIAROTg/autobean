import collections
import contextlib
import dataclasses
import decimal
import inspect
import re
import shlex
from typing import Any, Callable, ClassVar, Generic, Iterable, Iterator, NewType, Optional, Type, TypeVar, Union, get_args, get_origin
from beancount.core.data import Custom, Directive
from beancount.core.amount import Amount
from beancount.core import account as beancount_account
from beancount.parser import grammar
from autobean.utils import error_lib

Account = NewType('Account', str)
Currency = NewType('Currency', str)
_HANDLER_ATTR = '_autobean_handler'
_T = TypeVar('_T', bound=Directive)
_R = TypeVar('_R', bound=Iterable[Directive])
_Plugin = TypeVar('_Plugin', bound='BasePlugin')
_RegularHandlerImpl = Callable[[_Plugin, _T], _R]
_CustomHandlerImpl = Callable[..., _R]  # (self, custom, *args)


@dataclasses.dataclass(frozen=True)
class _RegularHandler(Generic[_Plugin, _T, _R]):
    directive_type: Type[Directive]
    when: Optional[Callable[[_Plugin], bool]]
    impl: _RegularHandlerImpl[_Plugin, _T, _R]


@dataclasses.dataclass(frozen=True)
class _CustomHandler:
    custom_type: str
    params_description: str
    params: list[inspect.Parameter]
    impl: _CustomHandlerImpl


class BasePlugin:
    _NAME: ClassVar[str]
    _ARGUMENT_TYPE: ClassVar[Any]
    _CUSTOM_SCOPE: ClassVar[Optional[re.Pattern]]
    _REGULAR_HANDLERS: ClassVar[dict[int, _RegularHandler]]
    _CUSTOM_HANDLERS: ClassVar[dict[str, list[_CustomHandler]]]

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
            for chandler in handlers:
                if (args := _get_args(entry.values or [], chandler)) is not None:
                    with _wrap_plugin_exception(entry, self._error_logger):
                        yield from chandler.impl(self, entry, *args)
                    return
            self._error_logger.log_error(
                error_lib.InvalidDirectiveError(
                    entry.meta,
                    f'Invalid arguments: {shlex.quote(entry.type)} expects {chandler.params_description}.',
                    entry))
            return
        if rhandler := self._REGULAR_HANDLERS.get(id(type(entry))):
            if rhandler.when is not None and not rhandler.when(self):
                return
            with _wrap_plugin_exception(entry, self._error_logger):
                yield from rhandler.impl(self, entry)
            return
        yield entry
        if isinstance(entry, Custom) and (
                self._CUSTOM_SCOPE is not None and self._CUSTOM_SCOPE.match(entry.type)):
            self._error_logger.log_error(
                error_lib.InvalidDirectiveError(
                    entry.meta, f'Unrecognized custom directive {shlex.quote(entry.type)}.', entry))
            return


@contextlib.contextmanager
def _wrap_plugin_exception(entry: Directive, error_logger: error_lib.ErrorLogger) -> Iterator[None]:
    try:
        yield
    except error_lib.PluginException as e:
        error_logger.log_error(error_lib.PluginError(
            e.meta or entry.meta, str(e), entry))


def _get_args(
        values: list[grammar.ValueType],
        handler: _CustomHandler,
) -> Optional[list[Any]]:
    queue = values[::-1]
    args = []
    for param in handler.params:
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
            handler = getattr(func, _HANDLER_ATTR, None)
            if isinstance(handler, _RegularHandler):
                regular_handlers[id(handler.directive_type)] = handler
            elif isinstance(handler, _CustomHandler):
                custom_handlers[handler.custom_type].append(handler)
        cls._REGULAR_HANDLERS = regular_handlers
        cls._CUSTOM_HANDLERS = custom_handlers
        return cls
    return decorator


def handle(
        directive_type: Type[_T],
        *,
        when: Optional[Callable[[_Plugin], bool]] = None,
) -> Callable[[_RegularHandlerImpl[_Plugin, _T, _R]], _RegularHandlerImpl[_Plugin, _T, _R]]:
    def decorator(impl: _RegularHandlerImpl[_Plugin, _T, _R]) -> _RegularHandlerImpl[_Plugin, _T, _R]:
        setattr(impl, _HANDLER_ATTR, _RegularHandler(directive_type, when, impl))
        return impl
    return decorator


def handle_custom(custom_type: str, params_description: str) -> Callable[[_CustomHandlerImpl], _CustomHandlerImpl]:
    def decorator(impl: _CustomHandlerImpl) -> _CustomHandlerImpl:
        setattr(impl, _HANDLER_ATTR, _CustomHandler(
            custom_type=custom_type,
            params_description=params_description,
            params=list(inspect.signature(impl).parameters.values())[2:],
            impl=impl))
        return impl
    return decorator
