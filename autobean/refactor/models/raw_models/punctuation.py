from . import internal


@internal.token_model
class Newline(internal.SimpleRawTokenModel):
    RULE = '_NL'


@internal.token_model
class Indent(internal.SimpleRawTokenModel):
    RULE = 'INDENT'


@internal.token_model
class Whitespace(internal.SimpleRawTokenModel):
    RULE = 'WS_INLINE'


@internal.token_model
class InlineComment(internal.SimpleRawTokenModel):
    RULE = 'COMMENT_INLINE'


@internal.token_model
class LineComment(internal.SimpleRawTokenModel):
    RULE = 'COMMENT_LINE'
