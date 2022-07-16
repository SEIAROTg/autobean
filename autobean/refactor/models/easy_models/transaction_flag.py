from autobean.refactor.models.raw_models import transaction_flag
from autobean.refactor.models.raw_models import asterisk
from autobean.refactor.models.raw_models import txn
from autobean.refactor.models.raw_models import flag


class TransactionFlag(transaction_flag.TransactionFlag):

    @property
    def raw_text(self) -> str:
        return self.raw_flag.raw_text
    
    @raw_text.setter
    def raw_text(self, raw_text: str) -> None:
        if raw_text == '*':
            self.raw_flag = asterisk.Asterisk.from_raw_text(raw_text)
        elif raw_text == 'txn':
            self.raw_flag = txn.Txn.from_raw_text(raw_text)
        else:
            self.raw_flag = flag.Flag.from_raw_text(raw_text)

    @property
    def value(self) -> str:
        raw_text = self.raw_text
        if raw_text == 'txn':
            return '*'
        return raw_text

    @value.setter
    def value(self, value: str) -> None:
        self.raw_text = value
