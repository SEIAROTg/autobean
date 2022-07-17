from . import internal


@internal.token_model
class Null(internal.SimpleRawTokenModel):
    RULE = 'NULL'
