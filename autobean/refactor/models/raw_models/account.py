from . import base
from . import internal


@base.token_model
class Account(internal.SimpleSingleValueRawTokenModel):
    RULE = 'ACCOUNT'
