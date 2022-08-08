import decimal
from typing import Optional, Type, TypeVar
from . import internal
from .generated import posting
from .generated.posting import PriceAnnotation
from .account import Account
from .cost_spec import CostSpec
from .currency import Currency
from .number_expr import NumberExpr
from .posting_flag import PostingFlag
from .punctuation import Indent

_Self = TypeVar('_Self', bound='Posting')


@internal.tree_model
class Posting(posting.Posting):

    @classmethod
    def from_value(
            cls: Type[_Self],
            account: str,
            number: Optional[decimal.Decimal] = None,
            currency: Optional[str] = None,
            cost: Optional[CostSpec] = None,
            price: Optional[PriceAnnotation] = None,
            *,
            indent: str = '    ',
            flag: Optional[str] = None,
    ) -> _Self:
        return cls.from_children(
            Indent.from_raw_text(indent),
            PostingFlag.from_raw_text(flag) if flag else None,
            Account.from_value(account),
            NumberExpr.from_value(number) if number is not None else None,
            Currency.from_value(currency) if currency is not None else None,
            cost,
            price,
        )
