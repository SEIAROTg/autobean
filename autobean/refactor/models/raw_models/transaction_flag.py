from . import internal


@internal.token_model
class TransactionFlag(internal.SingleValueRawTokenModel[str]):
    RULE = 'TRANSACTION_FLAG'

    @classmethod
    def _parse_value(cls, raw_text: str) -> str:
        if raw_text == 'txn':
            return '*'
        return raw_text

    @classmethod
    def _format_value(cls, value: str) -> str:
        return value
