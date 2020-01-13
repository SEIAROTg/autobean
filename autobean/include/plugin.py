from typing import List, Dict, Tuple, Set
from collections import namedtuple
import os.path
from beancount.core.data import Directive, Custom
from beancount import loader
from autobean.utils.plugin_base import PluginBase


def plugin(entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
    plugin = IncludePlugin()
    return plugin.process(entries, options)


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')


class IncludePlugin(PluginBase):
    _includes: Set[str]

    def __init__(self):
        super().__init__()
        self._includes = set()

    def process(self, entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
        self._includes = set(options['include'])
        ret = []
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.include':
                ret.extend(self.process_include_directive(entry))
            else:
                ret.append(entry)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)
        return ret, self._errors

    def process_include_directive(self, entry: Custom) -> List[Directive]:
        if len(entry.values) != 1:
            self._error(InvalidDirectiveError(
                entry.meta, 'autobean.include expects 1 argument but {} are given'.format(len(entry.values)), entry
            ))
            return []
        if entry.values[0].dtype is not str:
            self._error(InvalidDirectiveError(
                entry.meta, 'autobean.include expects a path as argument', entry
            ))
            return []
        path = entry.values[0].value
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        entries, errors, _ = loader.load_file(path)
        self._loading_errors(errors, entry.meta, entry)
        self._includes.add(path)
        return entries
