from typing import Type, TypeVar
from autobean.refactor.models.raw_models import include
from autobean.refactor.models.raw_models.include import IncludeLabel
from . import internal
from .escaped_string import EscapedString

internal.token_model(IncludeLabel)

_Self = TypeVar('_Self', bound='Include')


@internal.tree_model
class Include(include.Include):
    filename = internal.required_string_property(include.Include.raw_filename)

    @classmethod
    def from_value(cls: Type[_Self], filename: str) -> _Self:
        return cls.from_children(EscapedString.from_value(filename))
