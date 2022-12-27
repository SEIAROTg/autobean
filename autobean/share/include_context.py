"""Shared context between including and included files."""

import collections
import contextlib
import dataclasses
import threading
from typing import DefaultDict, Iterator

_THREAD_LOCAL = threading.local()


@dataclasses.dataclass(frozen=True)
class IncludeContext:
    viewpoint: str
    subaccounts: DefaultDict[str, set[str]] = dataclasses.field(
        default_factory=lambda: collections.defaultdict(set))


@contextlib.contextmanager
def try_enter_context(context: IncludeContext) -> Iterator[IncludeContext]:
    original_context = getattr(_THREAD_LOCAL, 'include_context', None)
    try:
        if original_context:
            yield original_context
        else:
            _THREAD_LOCAL.include_context = context
            yield context
    finally:
        _THREAD_LOCAL.include_context = original_context
