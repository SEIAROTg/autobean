from typing import List, Dict, Tuple
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
    def process(self, entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
        ret = []
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.include':
                ret.extend(self.process_include_directive(entry))
            else:
                ret.append(entry)
        ret.sort(key=lambda e: e.date)
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
        path = os.path.join(os.path.dirname(entry.meta['filename']), entry.values[0].value)
        entries, errors, _ = loader.load_file(path)
        self._errors += errors
        return entries
