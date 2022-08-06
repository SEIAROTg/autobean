from typing import Type, TypeVar
from .generated import poptag
from .generated.poptag import PoptagLabel
from . import internal
from .tag import Tag

_Self = TypeVar('_Self', bound='Poptag')


@internal.tree_model
class Poptag(poptag.Poptag):

    @classmethod
    def from_value(cls: Type[_Self], tag: str) -> _Self:
        return cls.from_children(Tag.from_value(tag))
