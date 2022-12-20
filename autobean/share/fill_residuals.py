from typing import Any
from collections import defaultdict
from beancount.core.data import Directive, Transaction
from beancount.core import interpolate
from autobean.share import utils


def fill_residuals(entries: list[Directive], options: dict[str, Any]) -> list[Directive]:
    ret = []
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            continue
        original_residual = interpolate.compute_residual(entry.postings)
        tolerances = interpolate.infer_tolerances(entry.postings, options)
        if not original_residual.is_small(tolerances):
            # The original transaction was not balanced, skip as we don't know what to do.
            ret.append(entry)
            continue
        postings = entry.postings[:]
        postings_by_party = defaultdict(list)
        for posting in entry.postings:
            party = posting.account.rsplit(':', 1)[1].strip('[]')
            postings_by_party[party].append(posting)
        for party, party_postings in postings_by_party.items():
            residual = interpolate.compute_residual(party_postings)
            # Use square brackets in account name to avoid collision with actual accounts
            subaccount = f'[Residuals]:[{party}]'
            postings += utils.get_residual_postings(residual, subaccount)
        ret.append(entry._replace(postings=postings))
    return ret
