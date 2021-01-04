from typing import List, Dict, Any
from collections import defaultdict
from beancount.core.data import Directive, Transaction
from beancount.core import interpolate
from autobean.share import utils


def fill_residuals(entries: List[Directive], options: Dict[str, Any]) -> List[Directive]:
    ret = []
    for entry in entries:
        if not isinstance(entry, Transaction):
            ret.append(entry)
            continue
        # Create residual postings for each party and add up all postings into real accounts
        # If the original transaction was not balanced we book residuals to error account
        # so we don't accidentially make it looks balanced for a subaccount in some cases.
        original_residual = interpolate.compute_residual(entry.postings)
        tolerances = interpolate.infer_tolerances(entry.postings, options)
        if original_residual.is_small(tolerances):
            subaccount_tmpl = '[Residuals]:[{}]'
        else:
            subaccount_tmpl = '[Error]:[{}]'
        postings = entry.postings[:]
        postings_by_party = defaultdict(list)
        for posting in entry.postings:
            party = posting.account.rsplit(':', 1)[1].strip('[]')
            postings_by_party[party].append(posting)
        for party, party_postings in postings_by_party.items():
            residual = interpolate.compute_residual(party_postings)
            # Use square brackets in account name to avoid collision with actual accounts
            subaccount = subaccount_tmpl.format(party)
            postings += utils.get_residual_postings(residual, subaccount)
        ret.append(entry._replace(postings=postings))
    return ret
