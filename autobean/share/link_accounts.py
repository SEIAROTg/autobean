import collections
import dataclasses
import datetime
import decimal
import re
from typing import Any, Iterable, Optional
from beancount.core import amount
from beancount.core.data import Custom, Directive, Transaction, filter_txns, iter_entry_dates
from autobean.utils import error_lib


_MAIN_ACCOUNT_REGEX = re.compile(r':\[.*\]$')


@dataclasses.dataclass(frozen=True)
class Link:
    path: str
    account: str
    complement_path: str
    complement_account: str
    custom: Custom


class UnresolvedLinkError(error_lib.Error):
    pass


def link_accounts(
        entries_by_file: dict[str, list[Directive]],
        links: Iterable[Link],
        logger: error_lib.ErrorLogger) -> list[Directive]:

    _check_links(entries_by_file, links, logger)
    edges = _build_graph(entries_by_file, links, logger)
    return _resolve_links(entries_by_file, edges, logger)


def _main_account(account: str) -> str:
    return re.sub(_MAIN_ACCOUNT_REGEX, '', account)


def _check_links(
        entries_by_file: dict[str, list[Directive]],
        links: Iterable[Link],
        logger: error_lib.ErrorLogger) -> None:
    all_endpoints = set()
    for link in links:
        endpoints = [
            (link.path, link.account),
            (link.complement_path, link.complement_account),
        ]
        for ep in endpoints:
            if ep in all_endpoints:
                logger.log_error(error_lib.InvalidDirectiveError(
                    link.custom.meta,
                    f'Account {ep[1]} in {ep[0]} has multiple links',
                    link.custom,
                ))
            if ep[0] not in entries_by_file:
                logger.log_error(error_lib.InvalidDirectiveError(
                    link.custom.meta,
                    f'Ledger {ep[0]} was not included with '
                    f'"autobean.share.include" from this ledger',
                    link.custom,
                ))
            all_endpoints.add(ep)


def _build_graph(
        entries_by_file: dict[str, list[Directive]],
        links: Iterable[Link],
        logger: error_lib.ErrorLogger) -> dict[int, list[tuple[Transaction, str]]]:

    day = datetime.timedelta(days=1)
    edges = collections.defaultdict(list) # id(txn) -> [(complement txn, account)]
    for link in links:
        entries = entries_by_file.get(link.path, [])
        complement_entries = entries_by_file.get(link.complement_path, [])

        for entry in filter_txns(entries):
            expected_complement_feature = _transaction_feature(
                entry, link.account, True)
            if not expected_complement_feature[1]:
                continue
            # find complement txn and check duplicated complement
            complement_txn = None
            complement_duplicated = False
            for complement_entry in filter_txns(iter_entry_dates(
                    complement_entries, entry.date, entry.date + day)):
                complement_feature = _transaction_feature(
                    complement_entry, link.complement_account, False)
                if complement_feature == expected_complement_feature:
                    if not complement_txn:
                        complement_txn = complement_entry
                    else:
                        complement_duplicated = True
                        break
            # check duplicated
            duplicated = False
            found = False
            feature = _transaction_feature(entry, link.account, False)
            for entry2 in filter_txns(iter_entry_dates(
                    entries, entry.date, entry.date + day)):
                feature2 = _transaction_feature(entry2, link.account, False)
                if feature2 == feature:
                    if found:
                        duplicated = True
                        break
                    found = True
            if not complement_txn:
                logger.log_error(UnresolvedLinkError(
                    entry.meta,
                    f'No complement transaction found for link {link}',
                    entry,
                ))
            elif complement_duplicated:
                logger.log_error(UnresolvedLinkError(
                    entry.meta,
                    f'Multiple complement transactions found for link {link}',
                    entry,
                ))
            elif duplicated:
                logger.log_error(UnresolvedLinkError(
                    complement_txn.meta,
                    f'Multiple complement transactions found for link {link}',
                    complement_txn,
                ))
            else:
                edges[id(entry)].append((complement_txn, link.account))
                edges[id(complement_txn)].append((entry, link.complement_account))

        for complement_txn in filter_txns(complement_entries):
            complement_feature = _transaction_feature(
                complement_txn, link.complement_account, False)
            if complement_feature[1] and id(complement_txn) not in edges:
                logger.log_error(UnresolvedLinkError(
                    complement_txn.meta,
                    f'No complement transaction found for link {link}',
                    complement_txn,
                ))

    return edges


def _resolve_links(
        entries_by_file: dict[str, list[Directive]],
        edges: dict[int, list[tuple[Transaction, str]]],
        logger: error_lib.ErrorLogger,
) -> list[Directive]:
    ret = []
    all_visited = set()
    bad = set()
    for entries in entries_by_file.values():
        for entry in entries:
            if id(entry) in all_visited:
                continue
            if id(entry) not in edges or id(entry) in bad:
                ret.append(entry)
                continue

            q = collections.deque([entry])
            visited = set()
            txns = []
            while q:
                u = q.popleft()
                if id(u) in visited:
                    continue
                visited.add(id(u))
                txns.append(u)
                for edge in edges[id(u)]:
                    q.append(edge[0])
            merged_txn = merge_transactions(txns, edges, logger)
            if merged_txn:
                ret.append(merged_txn)
                all_visited.update(visited)
            else:
                ret.append(entry)
                bad.update(visited)
    return ret


def _transaction_feature(
        entry: Transaction,
        account: str,
        negated: bool,
) -> tuple[Optional[str], collections.Counter]:
    link_key = entry.meta.get('share_link_key', None)

    posting_features = []
    for posting in entry.postings:
        if _main_account(posting.account) != account:
            continue
        if negated:
            units = amount.mul(posting.units, decimal.Decimal(-1))
        else:
            units = posting.units
        posting_features.append(units)
    return link_key, collections.Counter(posting_features)


def merge_transactions(
        txns: list[Transaction],
        edges: dict[int, list[tuple[Transaction, str]]],
        logger: error_lib.ErrorLogger,
) -> Optional[Transaction]:
    date = None
    flag = None
    payee = None
    narration = ''
    tags = set[str]()
    links = set[str]()
    meta = dict[str, Any]()
    postings = []
    compatible = True
    last_txn = None
    for txn in txns:
        last_txn = txn
        if date and txn.date and txn.date != date:
            compatible = False
        date = date or txn.date
        if flag and txn.flag and txn.flag != flag:
            compatible = False
        flag = flag or txn.flag
        if payee and txn.payee and txn.payee != payee:
            compatible = False
        payee = payee or txn.payee
        if narration and txn.narration and txn.narration != narration:
            compatible = False
        narration = narration or txn.narration
        for k, v in txn.meta.items():
            mv = meta.get(k)
            meta[k] = mv or v
            if mv and mv != v and k not in ('filename', 'lineno'):
                compatible = False
                break
        if not compatible:
            break
        accounts_to_remove = set(edge[1] for edge in edges[id(txn)])
        for posting in txn.postings:
            if _main_account(posting.account) not in accounts_to_remove:
                postings.append(posting)

    if not compatible and last_txn:
        logger.log_error(UnresolvedLinkError(
            last_txn.meta,
            'Transaction and its complement do not agree on flag, payee, '
            'narration or meta',
            last_txn,
        ))
        return None
    txn = Transaction(
        date=date,
        meta=meta,
        flag=flag,
        payee=payee,
        narration=narration,
        tags=tags,
        links=links,
        postings=postings,
    )
    return txn
