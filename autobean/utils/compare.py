from collections import Counter
from beancount.core import data
from beancount.core.data import Directive
from beancount.core.compare import hash_entry


def compare_entries(entries1: list[Directive], entries2: list[Directive]) -> tuple[bool, list[Directive], list[Directive]]:
    """Compares two lists of entries.

    Similiar to beancount.core.comparer.compare_entries but allows duplicated entries
    """
    hashes1 = {
        hash_entry(entry, exclude_meta=True): entry for entry in entries1}
    hashes2 = {
        hash_entry(entry, exclude_meta=True): entry for entry in entries2}

    keys1 = Counter(hash_entry(entry, exclude_meta=True) for entry in entries1)
    keys2 = Counter(hash_entry(entry, exclude_meta=True) for entry in entries2)

    same = keys1 == keys2
    missing1 = data.sorted([hashes1[key] for key in keys1 - keys2])
    missing2 = data.sorted([hashes2[key] for key in keys2 - keys1])
    return same, missing1, missing2
