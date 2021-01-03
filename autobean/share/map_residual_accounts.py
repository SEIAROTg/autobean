import re
from typing import List
from beancount.core.data import Directive, Transaction
from autobean.utils.error_logger import ErrorLogger


RESIDUAL_ACCOUNT = 'Assets:Receivable'
ERROR_ACCOUNT = 'Equity:Error'


def map_residual_accounts(entries: List[Directive], logger: ErrorLogger) -> List[Directive]:
    ret = []
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            continue
        ret_postings = []
        for posting in entry.postings:
            account = posting.account
            account = re.sub(r'^\[Residuals\](?=:|$)', RESIDUAL_ACCOUNT.replace('\\', '\\\\'), account)
            account = re.sub(r'^\[Error\](?=:|$)', ERROR_ACCOUNT.replace('\\', '\\\\'), account)
            posting = posting._replace(
                account=account
            )
            ret_postings.append(posting)
        entry = entry._replace(
            postings=ret_postings,
        )
        ret.append(entry)
    return ret
