import re
from beancount.core.data import Directive, Transaction
from autobean.utils.error_lib import ErrorLogger


RESIDUAL_ACCOUNT = 'Assets:Receivable'


def map_residual_accounts(entries: list[Directive], logger: ErrorLogger) -> list[Directive]:
    ret = []
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            continue
        ret_postings = []
        for posting in entry.postings:
            account = posting.account
            account = re.sub(r'^\[Residuals\](?=:|$)', RESIDUAL_ACCOUNT.replace('\\', '\\\\'), account)
            posting = posting._replace(
                account=account
            )
            ret_postings.append(posting)
        entry = entry._replace(
            postings=ret_postings,
        )
        ret.append(entry)
    return ret
