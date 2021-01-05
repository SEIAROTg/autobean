from dataclasses import dataclass
from collections import namedtuple, defaultdict, deque, Counter
from datetime import timedelta
from decimal import Decimal
import functools
from typing import Dict, List, Iterable, Tuple, Optional
from beancount.core import amount
from beancount.core.data import Directive, Transaction, Custom, filter_txns, iter_entry_dates
from beancount.core.account import TYPE as ACCOUNT_TYPE
from autobean.utils.error_logger import ErrorLogger
from autobean.share import utils


InvalidDirectiveError = namedtuple('InvalidDirectiveError', 'source message entry')
UnresolvedLinkError = namedtuple('UnresolvedLinkError', 'source message entry')


@dataclass(repr=False, frozen=True)
class Link:
    directive: Custom

    @functools.cached_property
    def _values(self) -> Tuple[str, str, str, str]:
        return tuple(v.value for v in self.directive.values)

    @property
    def filename(self) -> str:
        return self._values[0]

    @property
    def account(self) -> str:
        return self._values[1]
    
    @property
    def complement_filename(self) -> str:
        return self._values[2]
    
    @property
    def complement_account(self) -> str:
        return self._values[3]

    def __repr__(self) -> str:
        return str(self._values)
    
    def valid(self) -> bool:
        if len(self.directive.values) != 4:
            return False
        if (tuple(v.dtype for v in self.directive.values) !=
                (str, ACCOUNT_TYPE, str, ACCOUNT_TYPE)):
            return False
        return True


def link_accounts(
        entries_by_file: Dict[str, List[Directive]],
        links: Iterable[Link],
        logger: ErrorLogger) -> List[Directive]:

    _check_links(entries_by_file, links, logger)
    edges = _build_graph(entries_by_file, links, logger)
    return _resolve_links(entries_by_file, edges, logger)


def _check_links(
        entries_by_file: Dict[str, List[Directive]],
        links: Iterable[Link],
        logger: ErrorLogger):
    all_endpoints = set()
    for link in links:
        if not link.valid():
            logger.log_error(InvalidDirectiveError(
                link.directive.meta,
                'autobean.share.link expects {filename} {account} '
                '{complement filename} {complement account} as arguments',
                link.directive,
            ))
            continue
        endpoints = [
            (link.filename, link.account),
            (link.complement_filename, link.complement_account),
        ]
        for ep in endpoints:
            if ep in all_endpoints:
                logger.log_error(InvalidDirectiveError(
                    link.directive.meta,
                    f'Account {ep[1]} in {ep[0]} has multiple links',
                    link.directive,
                ))
            if ep[0] not in entries_by_file:
                logger.log_error(InvalidDirectiveError(
                    link.directive.meta,
                    f'Ledger {ep[0]} was not included with '
                    f'"autobean.share.include" from this ledger',
                    link.directive,
                ))
            all_endpoints.add(ep)


def _build_graph(
        entries_by_file: Dict[str, List[Directive]],
        links: Iterable[Link],
        logger: ErrorLogger) -> Dict[int, List[Tuple[Transaction, str]]]:

    day = timedelta(days=1)
    edges = defaultdict(list) # id(txn) -> [(complement txn, account)]
    for link in links:
        if not link.valid():
            continue
        entries = entries_by_file.get(link.filename, [])
        complement_entries = entries_by_file.get(link.complement_filename, [])

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
        entries_by_file: Dict[str, List[Directive]],
        edges: Dict[int, List[Tuple[Transaction, str]]],
        logger: ErrorLogger) -> List[Directive]:
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

            q = deque([entry])
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
        negated: bool) -> Tuple[Optional[str], Counter]:
    link_key = entry.meta.get('share_link_key', None)

    posting_features = []
    for posting in entry.postings:
        if utils.main_account(posting.account) != account:
            continue
        if negated:
            units = amount.mul(posting.units, Decimal(-1))
        else:
            units = posting.units
        posting_features.append(units)
    return link_key, Counter(posting_features)


def merge_transactions(
        txns: List[Transaction],
        edges: Dict[int, Tuple[Transaction, str]],
        logger: ErrorLogger) -> Optional[Transaction]:
    date = None
    flag = None
    payee = None
    narration = ''
    tags = set()
    links = set()
    meta = {}
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
            mv = meta.get(k, None)
            meta[k] = mv or v
            if mv and mv != v and k not in ('filename', 'lineno'):
                compatible = False
                break
        if not compatible:
            break
        accounts_to_remove = set(edge[1] for edge in edges[id(txn)])
        for posting in txn.postings:
            if utils.main_account(posting.account) not in accounts_to_remove:
                postings.append(posting)

    if not compatible:
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
