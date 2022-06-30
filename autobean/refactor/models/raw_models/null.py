from . import base


@base.token_model
class Null(base.RawTokenModel):
    RULE = 'NULL'
