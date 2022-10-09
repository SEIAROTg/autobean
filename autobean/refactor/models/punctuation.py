from . import internal


@internal.token_model
class Eol(internal.SimpleDefaultRawTokenModel):
    RULE = 'EOL'
    DEFAULT = ''


@internal.token_model
class Indent(internal.SimpleSingleValueRawTokenModel, internal.DefaultRawTokenModel):
    RULE = 'INDENT'
    DEFAULT = ' ' * 4


@internal.token_model
class DedentMark(internal.SimpleDefaultRawTokenModel):
    RULE = 'DEDENT_MARK'
    DEFAULT = ''


@internal.token_model
class Comma(internal.SimpleDefaultRawTokenModel):
    RULE = '_COMMA'
    DEFAULT = ','


@internal.token_model
class Asterisk(internal.SimpleDefaultRawTokenModel):
    RULE = 'ASTERISK'
    DEFAULT = '*'
