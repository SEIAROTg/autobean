from . import internal


@internal.token_model
class PostingFlag(internal.SimpleSingleValueRawTokenModel):
    RULE = 'POSTING_FLAG'
