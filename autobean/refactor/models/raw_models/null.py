from . import internal


@internal.token_model
class Null(internal.SimpleDefaultRawTokenModel):
    RULE = 'NULL'
    DEFAULT = 'NULL'
