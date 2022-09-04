from typing import TypeVar
from . import base_token_models, spacing_accessors

_V = TypeVar('_V')


class SimpleRawTokenModel(
        base_token_models.SimpleRawTokenModel,
        spacing_accessors.SpacingAccessorsMixin):
    pass


class SingleValueRawTokenModel(
        base_token_models.SingleValueRawTokenModel[_V],
        spacing_accessors.SpacingAccessorsMixin):
    pass


class SimpleSingleValueRawTokenModel(
        base_token_models.SimpleSingleValueRawTokenModel,
        spacing_accessors.SpacingAccessorsMixin):
    pass


class DefaultRawTokenModel(
        base_token_models.DefaultRawTokenModel,
        spacing_accessors.SpacingAccessorsMixin):
    pass


class SimpleDefaultRawTokenModel(
        base_token_models.SimpleDefaultRawTokenModel,
        spacing_accessors.SpacingAccessorsMixin):
    pass
