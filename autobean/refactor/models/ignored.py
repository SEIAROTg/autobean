from . import internal


@internal.token_model
class Ignored(internal.SimpleRawTokenModel):
    RULE = 'IGNORED'
