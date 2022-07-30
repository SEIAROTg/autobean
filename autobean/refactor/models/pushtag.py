from typing import Type, TypeVar
from .generated import pushtag
from .generated.pushtag import PushtagLabel
from . import internal
from .tag import Tag

_Self = TypeVar('_Self', bound='Pushtag')


@internal.tree_model
class Pushtag(pushtag.Pushtag):
    tag = internal.required_string_property(pushtag.Pushtag.raw_tag)

    @classmethod
    def from_value(cls: Type[_Self], tag: str) -> _Self:
        return cls.from_children(Tag.from_value(tag))
