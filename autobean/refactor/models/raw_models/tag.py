from . import internal


@internal.token_model
class Tag(internal.SingleValueRawTokenModel[str]):
    RULE = 'TAG'

    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        return raw_text[1:]

    @classmethod
    def _format_value(cls, value: str) -> str:
        return f'#{value}'
