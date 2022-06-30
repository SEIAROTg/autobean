from . import base


@base.token_model
class Account(base.RawTokenModel):
    RULE = 'ACCOUNT'

    @classmethod
    def from_name(cls, name: str) -> 'Account':
        return cls.from_raw_text(name)

    @property
    def name(self) -> str:
        return self.raw_text

    @name.setter
    def name(self, name: str) -> None:
        self.raw_text = name
