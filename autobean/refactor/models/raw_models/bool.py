from . import internal


@internal.token_model
class Bool(internal.SingleValueRawTokenModel[bool]):
    RULE = 'BOOL'

    @classmethod
    def _parse_value(cls, raw_text: str) -> bool:
        return {
            'TRUE': True,
            'FALSE': False,
        }[raw_text]

    @classmethod
    def _format_value(cls, value: bool) -> str:
        return str(value).upper()
