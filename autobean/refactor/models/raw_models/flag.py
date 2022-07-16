from . import base
from . import internal


@base.token_model
class Flag(internal.SimpleSingleValueRawTokenModel):
    RULE = 'FLAG'
