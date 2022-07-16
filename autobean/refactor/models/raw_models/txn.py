from . import base


@base.token_model
class Txn(base.RawTokenModel):
    RULE = 'TXN'
