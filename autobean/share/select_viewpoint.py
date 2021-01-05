from collections import namedtuple
from decimal import Decimal
from typing import List, Optional
from beancount.core import amount
from beancount.core.data import Directive, Transaction, Balance, Pad
from autobean.utils.error_logger import ErrorLogger


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
DuplicatedOwnerError = namedtuple('InvalidDirectiveError', 'source message entry')


def select_viewpoint(entries: List[Directive], viewpoint: Optional[str], logger: ErrorLogger) -> List[Directive]:
    ret = []
    for entry in entries:
        if isinstance(entry, Balance) or isinstance(entry, Pad):
            continue
        if isinstance(entry, Transaction):
            entry = process_transaction(entry, viewpoint)
        if entry:
            ret.append(entry)
    return ret


def process_transaction(entry: Transaction, viewpoint: str) -> Optional[Transaction]:
    if viewpoint == 'everyone':
        return entry
    suffix = f':[{viewpoint}]'
    postings = []
    relevant = False
    for posting in entry.postings:
        if posting.account.startswith('[Residuals]:'):
            if not posting.account.endswith(suffix):
                postings.append(posting._replace(
                    units=amount.mul(posting.units, Decimal(-1)),
                ))
        else:
            if posting.account.endswith(suffix):
                postings.append(posting._replace(
                    account=posting.account.rsplit(':', 1)[0],
                ))
        if posting.account.endswith(suffix):
            relevant = True
    if postings:
        return entry._replace(
            flag=entry.flag if relevant else 'T',
            postings=postings,
        )
