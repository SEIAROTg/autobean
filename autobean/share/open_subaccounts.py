from collections import defaultdict
from beancount.core.data import Directive, Transaction, Open, Close
from autobean.utils.error_lib import ErrorLogger
from autobean.share import utils


def open_subaccounts(entries: list[Directive], logger: ErrorLogger) -> list[Directive]:
    subaccounts: defaultdict[str, set[str]] = defaultdict(set)
    for entry in entries:
        if not isinstance(entry, Transaction):
            continue
        for posting in entry.postings:
            if utils.is_subaccount(posting.account):
                subaccount = posting.account
                account = subaccount.rsplit(':', 1)[0]
                subaccounts[account].add(posting.account)
    ret = []
    for entry in entries:
        if not isinstance(entry, Open) and not isinstance(entry, Close):
            ret.append(entry)
            continue
        if not entry.account in subaccounts:
            ret.append(entry)
        for subaccount in subaccounts[entry.account]:
            ret.append(entry._replace(account=subaccount))
    return ret
