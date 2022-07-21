from . import internal


@internal.token_model
class MetaKey(internal.SingleValueRawTokenModel[str]):
    RULE = 'META_KEY'

    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        return raw_text[:-1]

    @classmethod
    def _format_value(cls, value: str) -> str:
        return f'{value}:'
