import dataclasses
from beancount.core.data import Custom, Directive
from autobean.utils import typed_custom


@dataclasses.dataclass(frozen=True)
class Include(typed_custom.TypedCustom):
    TYPE = 'autobean.share.include'
    ERROR_MESSAGE = f'{TYPE} expects exactly one path as argument'
    filename: str


@dataclasses.dataclass(frozen=True)
class Link(typed_custom.TypedCustom):
    TYPE = 'autobean.share.link'
    ERROR_MESSAGE = f'{TYPE} expects (filename, account, complement_filename, complement_account)'
    filename: str
    _account: typed_custom.Account
    complement_filename: str
    _complement_account: typed_custom.Account

    @property
    def account(self) -> str:
        return self._account.name

    @property
    def complement_account(self) -> str:
        return self._complement_account.name


@dataclasses.dataclass(frozen=True)
class SharePolicy(typed_custom.TypedCustom):
    TYPE = 'autobean.share.policy'
    ERROR_MESSAGE = f'{TYPE} expects exactly one string or account as argument'
    subject: str | typed_custom.Account


@dataclasses.dataclass(frozen=True)
class ProportionateAssertion(typed_custom.TypedCustom):
    TYPE = 'autobean.share.proportionate'
    ERROR_MESSAGE = f'{TYPE} expects exactly one account as argument'
    account: typed_custom.Account


def is_autobean_share_directive(entry: Directive) -> bool:
    return isinstance(entry, Custom) and (
        entry.type.startswith('autobean.share.') or entry.type == 'autobean.share')
