from .internal import registry as _registry
from .internal import base_token_models as _base_token_models


@_registry.token_model
class Newline(_base_token_models.SimpleDefaultRawTokenModel):
    RULE = '_NEWLINE'
    DEFAULT = '\n'


@_registry.token_model
class Whitespace(_base_token_models.SimpleDefaultRawTokenModel):
    RULE = 'WHITESPACE'
    DEFAULT = ' '
