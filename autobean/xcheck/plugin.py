from typing import List, Dict, Tuple, Iterator, Set
from collections import namedtuple, Counter
import os.path
import datetime
from beancount.core.data import Directive, Custom, Transaction, Balance, Posting
from beancount import loader
from beancount.ops.validation import ValidationError
import beancount.core.account
import beancount.ops.balance
from autobean.utils.plugin_base import PluginBase


def plugin(entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
    plugin = CrossCheckPlugin()
    return plugin.process(entries, options)


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
CrossCheckError = namedtuple('CrossCheckError', 'source message entry')


class PostingToCompare:
    posting: Posting
    transaction: Transaction

    def __init__(self, posting: Posting, transaction: Transaction):
        self.posting = posting
        self.transaction = transaction

    def __eq__(self, other):
        return self.transaction.date == other.transaction.date \
               and self.posting.account == other.posting.account \
               and self.posting.units == other.posting.units

    def __hash__(self):
        return hash((self.transaction.date, self.posting.account, self.posting.units))


class CrossCheckPlugin(PluginBase):
    _includes: Set[str]

    def __init__(self):
        super().__init__()
        self._includes = set()

    def process(self, entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
        self._includes = set(options['include'])
        generated_entries = []
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.xcheck':
                generated_entries += self.process_xcheck_directive(entry, entries)
        # Allow tools to refresh data when included files are updated.
        options['include'] = list(self._includes)
        return entries + generated_entries, self._errors

    def process_xcheck_directive(self, entry: Custom, entries: List[Directive]) -> List[Directive]:
        if len(entry.values) < 2:
            self._error(InvalidDirectiveError(
                entry.meta, 'autobean.xcheck expects at least 2 arguments but 1 is given', entry
            ))
            return []
        if entry.values[0].dtype is not str \
                or entry.values[1].dtype is not datetime.date \
                or any(arg.dtype != beancount.core.account.TYPE for arg in entry.values[2:]):
            self._error(InvalidDirectiveError(
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
            self._loading_errors(stmt_errors, entry.meta, entry)
            return []

        entries = self.filter_by_time_period(entries, start, end)
        stmt_entries = self.filter_by_time_period(stmt_entries, start, end)
        postings = list(self.extract_related_postings(entries, accounts))
        stmt_postings = list(self.extract_related_postings(stmt_entries, accounts))

        _, unexpected, missing = self.compare_postings(postings, stmt_postings)
        for posting in unexpected:
            self._error(CrossCheckError(
                posting.posting.meta, 'Unexpected posting', posting.transaction
            ))
        for posting in missing:
            self._error(CrossCheckError(
                posting.posting.meta, 'Missing posting', posting.transaction
            ))
        self._includes.add(path)
        return [entry for entry in stmt_entries if isinstance(entry, Balance)]

    @staticmethod
    def extract_related_postings(entries: List[Directive], accounts: Set[str]) -> Iterator[PostingToCompare]:
        for entry in entries:
            if not isinstance(entry, Transaction):
                continue
            for posting in entry.postings:
                if not accounts or posting.account in accounts:
                    yield PostingToCompare(posting, entry)

    @classmethod
    def compare_postings(cls, postings1: List[PostingToCompare], postings2: List[PostingToCompare]) -> Tuple[bool, List[PostingToCompare], List[PostingToCompare]]:
        missings2 = cls.find_missings(postings1, postings2)
        missings1 = cls.find_missings(postings2, postings1)
        same = not missings1 and not missings2
        return same, missings1, missings2

    @staticmethod
    def find_missings(postings1: List[PostingToCompare], postings2: List[PostingToCompare]) -> List[PostingToCompare]:
        hashed1 = Counter(postings1)
        missings2 = []
        for posting in postings2:
            if hashed1[posting]:
                hashed1[posting] -= 1
            else:
                missings2.append(posting)
        return missings2

    @staticmethod
    def filter_by_time_period(entries: List[Directive], start: datetime.date, end: datetime.date):
        return [entry for entry in entries if start <= entry.date < end]
