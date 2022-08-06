from typing import Type, TypeVar
from . import internal
from .meta_key import MetaKey
from .generated import popmeta
from .generated.popmeta import PopmetaLabel

_Self = TypeVar('_Self', bound='Popmeta')


@internal.tree_model
class Popmeta(popmeta.Popmeta):

    @classmethod
    def from_value(cls: Type[_Self], key: str) -> _Self:
        return cls.from_children(MetaKey.from_value(key))
