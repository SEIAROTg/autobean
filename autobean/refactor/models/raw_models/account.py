from . import base


@base.token_model
class Account(base.RawTokenModel):
    RULE = 'ACCOUNT'

    @property
    def name(self) -> str:
        return self.raw_text

    @name.setter
    def name(self, name: str) -> None:
        self.raw_text = name
