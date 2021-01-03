from typing import List
from beancount.core.data import Directive, Transaction
from autobean.utils.error_logger import ErrorLogger


RESIDUAL_ACCOUNT = 'Assets:Receivable'


def map_residual_accounts(entries: List[Directive], logger: ErrorLogger) -> List[Directive]:
    ret = []
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            continue
        ret_postings = []
        for posting in entry.postings:
            account = posting.account
            segs = account.split(':', 1)
            if segs[0] == '[Residuals]':
                if len(segs) == 1:
                    account = RESIDUAL_ACCOUNT
                else:
                    account = RESIDUAL_ACCOUNT + ':{}'.format(segs[1])
            posting = posting._replace(
                account=account
            )
            ret_postings.append(posting)
        entry = entry._replace(
            postings=ret_postings,
        )
        ret.append(entry)
    return ret
