from . import internal


@internal.token_model
class Currency(internal.SimpleSingleValueRawTokenModel):
    RULE = 'CURRENCY'
