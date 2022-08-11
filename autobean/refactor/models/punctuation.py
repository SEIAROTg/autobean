from . import internal


@internal.token_model
class Newline(internal.SimpleRawTokenModel):
    RULE = '_NL'


@internal.token_model
class Eol(internal.SimpleDefaultRawTokenModel):
    RULE = 'EOL'
    DEFAULT = ''


@internal.token_model
class Indent(internal.SimpleSingleValueRawTokenModel):
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


@internal.token_model
class Comma(internal.SimpleDefaultRawTokenModel):
    RULE = '_COMMA'
    DEFAULT = ','


@internal.token_model
class Asterisk(internal.SimpleDefaultRawTokenModel):
    RULE = 'ASTERISK'
    DEFAULT = '*'
