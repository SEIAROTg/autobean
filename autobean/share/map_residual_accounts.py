import re
from beancount.core.data import Close, Directive, Open, Transaction, new_metadata
from autobean.utils.error_lib import ErrorLogger


RESIDUAL_ACCOUNT = 'Assets:Receivable'
_RESIDUAL_ACCOUNT_REPL = fr'{re.escape(RESIDUAL_ACCOUNT)}:\1'


def map_residual_accounts(entries: list[Directive], logger: ErrorLogger) -> list[Directive]:
    ret = []
    open_accounts = set()
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            if isinstance(entry, Open):
                open_accounts.add(entry.account)
            elif isinstance(entry, Close):
                open_accounts.discard(entry.account)
            continue
        ret_postings = []
        for posting in entry.postings:
            account = posting.account
            account = re.sub(r'^\[Residuals\]:\[(.*)\]', _RESIDUAL_ACCOUNT_REPL, account)
            if account == posting.account:
                ret_postings.append(posting)
                continue
            posting = posting._replace(
                account=account)
            ret_postings.append(posting)
            if account not in open_accounts:
                ret.append(Open(
                    meta=new_metadata('', 0),
                    date=entry.date,
                    account=account,
                    currencies=None,
                    booking=None))
                open_accounts.add(account)
        entry = entry._replace(
            postings=ret_postings)
        ret.append(entry)
    return ret
