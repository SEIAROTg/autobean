from collections import Counter, defaultdict, deque
import copy
import datetime
from typing import Iterable

from beancount.core.data import Transaction, Directive, iter_entry_dates, filter_txns
from beancount.ingest.extract import DUPLICATE_META


_Node = tuple[bool, Directive]  # (is_new_entry, entry)


def guess_transaction_duplicated(
        new_transaction: Transaction,
        existing_transaction: Transaction) -> bool:
    """Provides a rough guess that a new transaction already exists.
    
    Returns True iff for all the accounts that the new transaction describes,
    all postings under that account are the same in terms of units between
    the two transactions.
    """

    relevant_accounts = {
        posting.account
        for posting in new_transaction.postings
    }
    relevant_existing_data = Counter(
        (posting.account, posting.units)
        for posting in existing_transaction.postings
        if posting.account in relevant_accounts
    )
    relevant_new_data = Counter(
        (posting.account, posting.units)
        for posting in new_transaction.postings
    )

    return relevant_existing_data == relevant_new_data


def deduplicate(
        new_entries: list[Directive],
        existing_entries: list[Directive],
        window_days: int = 10) -> list[Directive]:
    """De-duplicate entries.

    A new non-transaction entry is considered connected to an existing entry
    iff they are identical.
    
    A new transaction is considered connected to an existing transaction iff:
    * the new transaction is no earlier than the existing transaction.
    * the new transaction is at most {window_days} days later than the existing
      transaction.
    * guess_transaction_duplicated returns True.

    If a new entry doesn't have any connection, it's considered non-duplicated.

    For each strongly connected subgraph, if all new entries are matched, all
    of them are considered duplicated. Otherwise, all of them are considered
    possibly duplicated.

    Returns new entries where:
    * Non-duplicated entries are preserved.
    * Duplicated entries are removed.
    * Possibly-duplicated entries are marked with DUPLICATE_META.
    """
    window_head = datetime.timedelta(days=window_days)
    window_tail = datetime.timedelta(days=1)

    matcher = _Matcher()
    for new_entry in new_entries:
        if isinstance(new_entry, Transaction):
            for existing_entry in filter_txns(iter_entry_dates(
                    existing_entries,
                    new_entry.date - window_head,
                    new_entry.date + window_tail)):
                if guess_transaction_duplicated(new_entry, existing_entry):
                    matcher.add_edge(id(new_entry), id(existing_entry))
        else:
            for existing_entry in iter_entry_dates(
                    existing_entries,
                    new_entry.date,
                    new_entry.date + window_tail):
                if new_entry == existing_entry:
                    matcher.add_edge(id(new_entry), id(existing_entry))
    
    duplicates: set[Directive] = set()
    possibly_duplicates: set[Directive] = set()

    matches = matcher.matches()
    for subgraph in matcher.subgraphs():
        n = len([True for node in subgraph if node in matches])
        if n == len(subgraph):  # duplicated
            duplicates.update(node[1] for node in subgraph if node[0])
        elif n:  # possibly duplicated
            possibly_duplicates.update(node[1] for node in subgraph if node[0])

    ret = []
    for new_entry in new_entries:
        if id(new_entry) in duplicates:
            continue
        elif id(new_entry) in possibly_duplicates and hasattr(new_entry, 'meta'):
            meta = copy.deepcopy(new_entry.meta)
            meta[DUPLICATE_META] = True
            ret.append(new_entry._replace(meta=meta))
        else:
            ret.append(new_entry)

    return ret


class _Matcher:
    def __init__(self) -> None:
        self._new_nodes: set[_Node] = set()
        self._edges: defaultdict[_Node, set[_Node]] = defaultdict(set)

    def add_edge(self, new_entry: Directive, existing_entry: Directive) -> None:
        new_node = (True, new_entry)
        existing_node = (False, existing_entry)
        self._new_nodes.add(new_node)
        self._edges[new_node].add(existing_node)
        self._edges[existing_node].add(new_node)

    def matches(self) -> set[_Node]:
        matches = set()
        for new_node in self._new_nodes:
            if new_node in matches:
                continue
            q: deque[_Node] = deque()
            q.append(new_node)
            visited = set()
            while q:
                u = q.popleft()
                if u in visited:
                    continue
                visited.add(u)
                if u not in matches and u != new_node:
                    matches.add(new_node)
                    matches.add(u)
                    break
                for v in self._edges[u]:
                    q.append(v)
        return matches

    def subgraphs(self) -> Iterable[set[_Node]]:
        visited = set()
        for new_node in self._new_nodes:
            if new_node in visited:
                continue
            subgraph_nodes = set()
            q: deque[_Node] = deque()
            q.append(new_node)
            while q:
                u = q.popleft()
                if u in visited:
                    continue
                subgraph_nodes.add(u)
                visited.add(u)
                for v in self._edges[u]:
                    q.append(v)
            yield subgraph_nodes
