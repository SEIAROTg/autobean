from collections import namedtuple
from typing import List, Optional
from beancount.core.data import Directive, Balance, Transaction
from autobean.utils.error_logger import ErrorLogger
from autobean.share import utils


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
DuplicatedOwnerError = namedtuple('InvalidDirectiveError', 'source message entry')


def select_viewpoint(entries: List[Directive], viewpoint: Optional[str], logger: ErrorLogger) -> List[Directive]:
    ret = []
    for entry in entries:
        if isinstance(entry, Balance):
            continue
        if isinstance(entry, Transaction):
            entry = process_transaction(entry, viewpoint)
        if entry:
            ret.append(entry)
    return ret


def process_transaction(entry: Transaction, viewpoint: str) -> Optional[Transaction]:
    if viewpoint == 'everyone':
        return entry
    postings = [
        posting._replace(
            account=posting.account.rsplit(':', 1)[0],
        )
        for posting in entry.postings
        if posting.account.endswith(f':[{viewpoint}]')
    ]
    if postings:
        return entry._replace(
            postings=postings,
        )
