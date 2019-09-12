from typing import List
from beancount.loader import LoadError
from beancount.core.data import Meta, Directive


class PluginBase:
    _errors: List

    def __init__(self):
        self._errors = []

    def _error(self, error):
        self._errors.append(error)

    def _loading_errors(self, errors: List, meta: Meta, entry: Directive):
        for error in errors:
            if isinstance(error, LoadError):
                error = error._replace(source=meta, entry=entry)
            self._errors.append(error)
