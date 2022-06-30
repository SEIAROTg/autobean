from . import base
from . import internal


@base.token_model
class Currency(internal.SimpleSingleValueRawTokenModel):
    RULE = 'CURRENCY'
