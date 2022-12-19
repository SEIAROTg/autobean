import dataclasses
import os.path
from typing import Any
from beancount.core.data import Directive
from beancount import loader
from autobean.utils import error_lib, typed_custom
from autobean.utils.plugin_base import PluginBase


def plugin(entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list[error_lib.Error]]:
    plugin = IncludePlugin()
    return plugin.process(entries, options)


@dataclasses.dataclass(frozen=True)
class IncludeCustom(typed_custom.TypedCustom):
    TYPE = 'autobean.include'
    ERROR_MESSAGE = f'{TYPE} expects exactly one path as argument'
    path: str


class IncludePlugin(PluginBase):
    _includes: set[str]

    def __init__(self) -> None:
        super().__init__()
        self._includes = set()

    def process(self, entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list[error_lib.Error]]:
        self._includes = set(options['include'])
        ret = []
        for entry in entries:
            if include := IncludeCustom.try_parse(entry):
                if isinstance(include, error_lib.Error):
                    self._error_logger.log_error(include)
                    continue
                ret.extend(self.process_include_directive(include))
            else:
                ret.append(entry)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)
        return ret, self._error_logger.errors

    def process_include_directive(self, include: IncludeCustom) -> list[Directive]:
        path = os.path.join(os.path.dirname(include.custom.meta['filename']), include.path)
        entries, errors, _ = loader.load_file(path)
        self._error_logger.log_loading_errors(errors, include.custom)
        self._includes.add(path)
        return entries
