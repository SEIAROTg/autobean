import os.path
from typing import Any
from beancount.core.data import Directive, Custom
from beancount import loader
from autobean.utils import error_lib
from autobean.utils.plugin_base import PluginBase


def plugin(entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list[error_lib.Error]]:
    plugin = IncludePlugin()
    return plugin.process(entries, options)


class IncludePlugin(PluginBase):
    _includes: set[str]

    def __init__(self) -> None:
        super().__init__()
        self._includes = set()

    def process(self, entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list[error_lib.Error]]:
        self._includes = set(options['include'])
        ret = []
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.include':
                ret.extend(self.process_include_directive(entry))
            else:
                ret.append(entry)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)
        return ret, self._error_logger.errors

    def process_include_directive(self, entry: Custom) -> list[Directive]:
        if len(entry.values) != 1:
            self._error_logger.log_error(error_lib.InvalidDirectiveError(
                entry.meta, 'autobean.include expects 1 argument but {} are given'.format(len(entry.values)), entry
            ))
            return []
        if entry.values[0].dtype is not str:
            self._error_logger.log_error(error_lib.InvalidDirectiveError(
                entry.meta, 'autobean.include expects a path as argument', entry
            ))
            return []
        path = entry.values[0].value
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        entries, errors, _ = loader.load_file(path)
        self._error_logger.log_loading_errors(errors, entry)
        self._includes.add(path)
        return entries
