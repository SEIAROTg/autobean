from typing import List


class PluginBase:
    _errors: List

    def __init__(self):
        self._errors = []

    def _error(self, error):
        self._errors.append(error)
