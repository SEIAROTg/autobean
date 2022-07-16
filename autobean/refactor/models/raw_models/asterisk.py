from . import base


@base.token_model
class Asterisk(base.RawTokenModel):
    RULE = 'ASTERISK'
