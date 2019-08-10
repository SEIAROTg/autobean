from typing import List, Dict, Tuple, Iterator, Optional
from collections import namedtuple
import os.path
import datetime
from beancount.core.data import Directive, Custom, Transaction
from beancount import loader
import beancount.core.account
import beancount.ops.balance
from autobean.utils.compare import compare_entries


def plugin(entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
    plugin = CrossCheckPlugin(options)
    return plugin.process(entries)


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
CrossCheckError = namedtuple('CrossCheckError', 'source message entry')


class CrossCheckPlugin:
    errors: List

    def __init__(self, options: Dict):
        self.errors = []

    def process(self, entries: List[Directive]) -> Tuple[List[Directive], List]:
        for entry in entries:
            if isinstance(entry, Custom) and entry.type == 'autobean.xcheck':
                self.process_xcheck_directive(entry, entries)
        return entries, self.errors

    def process_xcheck_directive(self, entry: Custom, entries: List[Directive]):
        if len(entry.values) != 2:
            self.error(InvalidDirectiveError(
                entry.meta, 'Cross check expects 2 arguments but {} are given'.format(len(entry.values)), entry
            ))
            return
        if entry.values[0].dtype is not beancount.core.account.TYPE or entry.values[1].dtype is not str:
            self.error(InvalidDirectiveError(
                entry.meta, 'Cross check expects an account and a path as arguments', entry
            ))
            return
        account = entry.values[0].value
        path = os.path.join(os.path.dirname(entry.meta['filename']), entry.values[1].value)
        stmt_entries, stmt_errors, stmt_options = loader.load_file(path)
        if stmt_errors:
            self.errors += stmt_errors
            return
        transactions = list(filter_related_transactions(entries, account, entry.date))
        stmt_transactions = list(filter_related_transactions(stmt_entries, 'Assets:Account', entry.date, account))
        same, missings1, missings2 = compare_entries(transactions, stmt_transactions)
        for missing in missings1:
            self.error(CrossCheckError(
                missing.meta, 'Unexpected transaction', missing
            ))
        for missing in missings2:
            self.error(CrossCheckError(
                missing.meta, 'Missing transaction', missing
            ))

    def error(self, error):
        self.errors.append(error)


def filter_related_transactions(entries: List[Directive], account: str, date: datetime.date, rename_account: Optional[str] = None) -> Iterator[Transaction]:
    for entry in entries:
        if isinstance(entry, Transaction) and entry.date < date:
            postings = []
            for posting in entry.postings:
                if posting.account == account:
                    if rename_account is not None:
                        posting = posting._replace(account=rename_account)
                    postings.append(posting)
            if postings:
                yield entry._replace(
                    postings=postings,
                    flag='*',
                )
