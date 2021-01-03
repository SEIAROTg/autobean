from typing import List
from beancount.loader import LoadError
from beancount.core.data import Directive


class ErrorLogger:
    errors: List

    def __init__(self):
        self.errors = []

    def log_error(self, error):
        self.errors.append(error)

    def log_errors(self, errors: List):
        self.errors.extend(errors)

    def log_loading_errors(self, errors: List, entry: Directive):
        for error in errors:
            if isinstance(error, LoadError):
                error = error._replace(
                    source=entry.meta,
                    entry=entry,
                )
            self.errors.append(error)
