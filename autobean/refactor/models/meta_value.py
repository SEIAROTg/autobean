import datetime
import decimal
from typing import Union
from .account import Account
from .amount import Amount
from .bool import Bool
from .currency import Currency
from .date import Date
from .escaped_string import EscapedString
from .null import Null
from .number_expr import NumberExpr
from .tag import Tag

MetaRawValue = Account | Amount | Bool | Currency | Date | EscapedString | Null | NumberExpr | Tag
_ValueTypeSimplified = str | datetime.date | decimal.Decimal | bool
_ValueTypePreserved = Account | Currency | Tag | Null | Amount
MetaValue = Union[_ValueTypeSimplified, _ValueTypePreserved]
