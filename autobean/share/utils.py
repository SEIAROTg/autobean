from typing import Iterator, Union
from decimal import Decimal
from beancount.core.data import Posting, Directive, Custom
from beancount.core.amount import Amount, mul as amount_mul, div as amount_div
from beancount.core.position import CostSpec
from beancount.core.inventory import Inventory


def amount_distrib(amount: Amount, weight: Decimal, total_weight: Decimal):
    return amount_div(amount_mul(amount, weight), total_weight)


def costspec_distrib(costspec: CostSpec, weight: Decimal, total_weight: Decimal):
    number_total = costspec.number_total
    if number_total is not None:
        amount = Amount(number_total, costspec.currency)
        number_total = amount_distrib(amount, weight, total_weight)
    return costspec._replace(
        number_total = number_total
    )


def posting_distrib(posting: Posting, weight: Decimal, total_weight: Decimal):
    units = amount_distrib(posting.units, weight, total_weight)
    cost = posting.cost
    if isinstance(cost, CostSpec):
        cost = costspec_distrib(cost, weight, total_weight)
    return posting._replace(
        units=units,
        cost=cost,
    )


def get_residual_postings(residual: Inventory, account_rounding: str):
    return [
        Posting(
            account=account_rounding,
            units=-position.units,
            cost=position.cost,
            price=None,
            flag=None,
            meta={}
        )
        for position in residual
    ]


def is_share_policy_directive(entry: Directive):
    return isinstance(entry, Custom) and entry.type == 'autobean.share.policy'


def is_proportionate_assertion_directive(entry: Directive):
    return isinstance(entry, Custom) and entry.type == 'autobean.share.proportionate'


def is_include_directive(entry: Directive):
    return isinstance(entry, Custom) and entry.type == 'autobean.share.include'


def is_autobean_share_directive(entry: Directive):
    return isinstance(entry, Custom) and (entry.type.startswith('autobean.share.') or entry.type == 'autobean.share')


def is_owner_directive(entry: Directive):
    return isinstance(entry, Custom) and entry.type == 'autobean.share.owner'


def is_subaccount(account: str):
    lastseg = account.rsplit(':', 1)[1]
    return lastseg.startswith('[') and lastseg.endswith(']')


def main_account(account: str):
    if is_subaccount(account):
        return account.rsplit(':', 1)[0]
    return account


def ancestor_accounts(account: str) -> Iterator[str]:
    segs = account.split(':')
    while segs:
        yield ':'.join(segs)
        segs.pop()


def strip_meta(entry: Union[Directive, Posting]):
    if not entry.meta:
        return entry
    meta = {
        k: v
        for k, v in entry.meta.items()
        if not k.startswith('share-') and k not in (
            'share_policy',
            'share_recursive',
            'share_prorata')
    }
    return entry._replace(meta=meta)
