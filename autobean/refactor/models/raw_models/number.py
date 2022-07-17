import decimal
from . import internal


@internal.token_model
class Number(internal.SingleValueRawTokenModel[decimal.Decimal]):
    RULE = 'NUMBER'

    @classmethod
    def _parse_value(cls, raw_text: str) -> decimal.Decimal:
        return decimal.Decimal(raw_text.replace(',', ''))
    
    @classmethod
    def _format_value(cls, value: decimal.Decimal) -> str:
        return str(value)
