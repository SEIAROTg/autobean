from typing import Type, TypeVar
from autobean.refactor.models.raw_models import pushtag
from autobean.refactor.models.raw_models.pushtag import PushtagLabel, PoptagLabel
from . import internal
from .tag import Tag

internal.token_model(PushtagLabel)
internal.token_model(PoptagLabel)

_SelfPushtag = TypeVar('_SelfPushtag', bound='Pushtag')
_SelfPoptag = TypeVar('_SelfPoptag', bound='Poptag')


@internal.tree_model
class Pushtag(pushtag.Pushtag):
    tag = internal.required_string_property(pushtag.Pushtag.raw_tag)

    @classmethod
    def from_value(cls: Type[_SelfPushtag], tag: str) -> _SelfPushtag:
        return cls.from_children(Tag.from_value(tag))


@internal.tree_model
class Poptag(pushtag.Poptag):
    tag = internal.required_string_property(pushtag.Poptag.raw_tag)

    @classmethod
    def from_value(cls: Type[_SelfPoptag], tag: str) -> _SelfPoptag:
        return cls.from_children(Tag.from_value(tag))
