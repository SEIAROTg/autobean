from typing import Any, Iterable
from collections import Counter
import os.path
import datetime
from beancount.core.data import Directive, Custom, Transaction, Balance, Posting
from beancount import loader
from beancount.ops.validation import ValidationError
import beancount.core.account
import beancount.ops.balance
from autobean.utils import error_lib
from autobean.utils.plugin_base import PluginBase


def plugin(entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list]:
    plugin = CrossCheckPlugin()
    return plugin.process(entries, options)


class CrossCheckError(error_lib.Error):
    pass


class PostingToCompare:
    posting: Posting
    transaction: Transaction

    def __init__(self, posting: Posting, transaction: Transaction):
        self.posting = posting
        self.transaction = transaction

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PostingToCompare) and
            self.transaction.date == other.transaction.date and
            self.posting.account == other.posting.account and
            self.posting.units == other.posting.units)

    def __hash__(self) -> int:
        return hash((self.transaction.date, self.posting.account, self.posting.units))


class CrossCheckPlugin(PluginBase):
    _includes: set[str]

    def __init__(self) -> None:
        super().__init__()
        self._includes = set()

    def process(self, entries: list[Directive], options: dict) -> tuple[list[Directive], list]:
        self._includes = set(options['include'])
        generated_entries = []
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.xcheck':
                generated_entries += self.process_xcheck_directive(entry, entries)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)
        return entries + generated_entries, self._error_logger.errors

    def process_xcheck_directive(self, entry: Custom, entries: list[Directive]) -> list[Balance]:
        if len(entry.values) < 2:
            self._error_logger.log_error(error_lib.InvalidDirectiveError(
                entry.meta, 'autobean.xcheck expects at least 2 arguments but 1 is given', entry
            ))
            return []
        if entry.values[0].dtype is not str \
                or entry.values[1].dtype is not datetime.date \
                or any(arg.dtype != beancount.core.account.TYPE for arg in entry.values[2:]):
            self._error_logger.log_error(error_lib.InvalidDirectiveError(
                entry.meta, 'autobean.xcheck expects a path, a start date and zero or more accounts as arguments', entry
            ))
            return []
        path = entry.values[0].value
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        start = entry.values[1].value
        end = entry.date
        accounts = {arg.value for arg in entry.values[2:]}
        stmt_entries, stmt_errors, _ = loader.load_file(path)
        stmt_errors = [error for error in stmt_errors if not isinstance(error, ValidationError)]
        if stmt_errors:
            self._error_logger.log_loading_errors(stmt_errors, entry)
            return []

        entries = _filter_by_time_period(entries, start, end)
        stmt_entries = _filter_by_time_period(stmt_entries, start, end)
        postings = list(_extract_related_postings(entries, accounts))
        stmt_postings = list(_extract_related_postings(stmt_entries, accounts))

        _, unexpected, missing = _compare_postings(postings, stmt_postings)
        for posting in unexpected:
            self._error_logger.log_error(CrossCheckError(
                posting.posting.meta, 'Unexpected posting', posting.transaction
            ))
        for posting in missing:
            self._error_logger.log_error(CrossCheckError(
                posting.posting.meta, 'Missing posting', posting.transaction
            ))
        self._includes.add(path)
        return [entry for entry in stmt_entries if isinstance(entry, Balance)]


def _extract_related_postings(entries: list[Directive], accounts: set[str]) -> Iterable[PostingToCompare]:
    for entry in entries:
        if not isinstance(entry, Transaction):
            continue
        for posting in entry.postings:
            if not accounts or posting.account in accounts:
                yield PostingToCompare(posting, entry)


def _compare_postings(postings1: list[PostingToCompare], postings2: list[PostingToCompare]) -> tuple[bool, list[PostingToCompare], list[PostingToCompare]]:
    missings2 = list(_find_missings(postings1, postings2))
    missings1 = list(_find_missings(postings2, postings1))
    same = not missings1 and not missings2
    return same, missings1, missings2


def _find_missings(postings1: Iterable[PostingToCompare], postings2: Iterable[PostingToCompare]) -> Iterable[PostingToCompare]:
    hashed1 = Counter(postings1)
    for posting in postings2:
        if hashed1[posting]:
            hashed1[posting] -= 1
        else:
            yield posting


def _filter_by_time_period(entries: Iterable[Directive], start: datetime.date, end: datetime.date) -> list[Directive]:
    return[entry for entry in entries if start <= entry.date < end]
