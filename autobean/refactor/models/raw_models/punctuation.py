from . import internal


@internal.token_model
class Newline(internal.SimpleRawTokenModel):
    RULE = '_NL'


@internal.token_model
class Indent(internal.SimpleRawTokenModel):
    RULE = 'INDENT'


@internal.token_model
class Whitespace(internal.SimpleDefaultRawTokenModel):
    RULE = 'WS_INLINE'
    DEFAULT = ' '


@internal.token_model
class InlineComment(internal.SimpleRawTokenModel):
    RULE = 'COMMENT_INLINE'


@internal.token_model
class LineComment(internal.SimpleRawTokenModel):
    RULE = 'COMMENT_LINE'
