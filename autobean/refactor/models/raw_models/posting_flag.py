from . import base
from . import internal


@base.token_model
class PostingFlag(internal.SimpleSingleValueRawTokenModel):
    RULE = 'POSTING_FLAG'
