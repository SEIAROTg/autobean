import re
import datetime
from . import internal


@internal.token_model
class Date(internal.SingleValueRawTokenModel[datetime.date]):
    RULE = 'DATE'

    @classmethod
    def _parse_value(cls, raw_text: str) -> datetime.date:
        y, m, d = map(int, re.split('[-/]', raw_text))
        return datetime.date(y, m, d)

    @classmethod
    def _format_value(cls, value: datetime.date) -> str:
        return value.strftime('%Y-%m-%d')
