from typing import Any
from beancount.core.data import Directive, Transaction
from autobean.narration import comments


def plugin(entries: list[Directive], options: dict[str, Any]) -> tuple[list[Directive], list]:
    filenames = collect_transaction_filenames(entries)
    comment_narrations = {
        filename: comments.extract_from_file(filename)
        for filename in filenames
    }
    return [merge_narration(entry, comment_narrations) for entry in entries], []


def collect_transaction_filenames(entries: list[Directive]) -> set[str]:
    return {
        entry.meta['filename']
        for entry in entries
        if isinstance(entry, Transaction) and 'filename' in entry.meta
    }


def merge_narration(entry: Directive, comment_narrations: dict[str, dict[int, str]]) -> Directive:
    if not isinstance(entry, Transaction):
        return entry
    narrations = []
    for posting in entry.postings:
        if posting.meta:
            narration = posting.meta.get('narration')
            comment_narration = comment_narrations[posting.meta.get('filename')].get(posting.meta.get('lineno'))
            if narration is None and comment_narration:
                posting.meta['narration'] = comment_narration
                narration = comment_narration
            if narration:
                narrations.append(narration.strip())
    if entry.narration:
        return entry
    return entry._replace(narration=' | '.join(narrations))
