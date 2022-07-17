from . import internal


@internal.token_model
class Account(internal.SimpleSingleValueRawTokenModel):
    RULE = 'ACCOUNT'
