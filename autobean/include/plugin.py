import os.path
from typing import Any, Iterable, Optional
from beancount.core.data import Custom, Directive
from beancount import loader
from autobean.utils import plugin_lib


@plugin_lib.plugin('autobean.include')
class IncludePlugin(plugin_lib.BasePlugin):
    _includes: set[str]

    def process(self, entries: list[Directive], options: dict[str, Any], arg: Optional[str]) -> Iterable[Directive]:
        self._includes = set(options['include'])
        yield from super().process(entries, options, arg)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)

    @plugin_lib.handle_custom('autobean.include', 'exactly one path')
    def _handle_include(self, custom: Custom, path: str) -> Iterable[Directive]:
        path = os.path.join(os.path.dirname(custom.meta['filename']), path)
        entries, errors, _ = loader.load_file(path)
        self._error_logger.log_loading_errors(errors, custom)
        self._includes.add(path)
        return entries
