from typing import List, Dict, Tuple
from beancount.core.data import Directive, Transaction


def plugin(entries: List[Directive], options: Dict) -> Tuple[List[Directive], List]:
    return [merge_narration(entry) for entry in entries], []


def merge_narration(entry: Directive):
    if not isinstance(entry, Transaction):
        return entry
    narrations = []
    if entry.narration:
        narrations.append(entry.narration)
    for posting in entry.postings:
        narration = posting.meta and posting.meta.get('narration')
        if narration:
            narrations.append(narration)
    return entry._replace(narration=' | '.join(narrations))
