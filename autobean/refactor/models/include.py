from typing import Type, TypeVar
from . import internal
from .escaped_string import EscapedString
from .generated import include
from .generated.include import IncludeLabel

_Self = TypeVar('_Self', bound='Include')


@internal.tree_model
class Include(include.Include):

    @classmethod
    def from_value(cls: Type[_Self], filename: str) -> _Self:
        return cls.from_children(EscapedString.from_value(filename))
