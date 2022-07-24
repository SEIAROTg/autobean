from autobean.refactor.models.raw_models.punctuation import Newline, Indent, Whitespace, InlineComment, LineComment
from . import internal

internal.token_model(Newline)
internal.token_model(Indent)
internal.token_model(Whitespace)
internal.token_model(InlineComment)
internal.token_model(LineComment)
