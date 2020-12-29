from typing import List
from collections import Counter
from beancount.core import data
from beancount.core.data import Directive
from beancount.core.compare import hash_entry


# This is similar to beancount.core.comparer.compare_entries but allows duplicated entries
def compare_entries(entries1: List[Directive], entries2: List[Directive]):
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
