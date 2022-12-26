from typing import Any, Iterable, Optional
from collections import Counter
import os.path
import datetime
from beancount.core.data import Directive, Custom, Transaction, Balance, Posting
from beancount import loader
from beancount.ops.validation import ValidationError
from autobean.utils import error_lib, plugin_lib


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


@plugin_lib.plugin('autobean.xcheck')
class CrossCheckPlugin(plugin_lib.BasePlugin):
    _includes: set[str]

    def process(self, entries: list[Directive], options: dict[str, Any], arg: Optional[str]) -> Iterable[Directive]:
        self._entries = entries
        self._includes = set(options['include'])
        yield from super().process(entries, options, arg)
        options['include'] = list(self._includes)

    @plugin_lib.handle_custom('autobean.xcheck', 'a path, a start date and zero or more accounts')
    def handle_xcheck(self, entry: Custom, path: str, start: datetime.date, *accounts_tuple: plugin_lib.Account) -> Iterable[Directive]:
        path = os.path.join(os.path.dirname(entry.meta['filename']), path)
        accounts = set[str](accounts_tuple)
        end = entry.date
        stmt_entries, stmt_errors, _ = loader.load_file(path)
        stmt_errors = [error for error in stmt_errors if not isinstance(error, ValidationError)]
        if stmt_errors:
            yield entry
            self._error_logger.log_loading_errors(stmt_errors, entry)
            return

        entries = _filter_by_time_period(self._entries, start, end)
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
        for stmt_entry in stmt_entries:
            if isinstance(stmt_entry, Balance):
                yield stmt_entry
        yield entry


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
