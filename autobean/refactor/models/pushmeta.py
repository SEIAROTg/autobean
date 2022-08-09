from typing import Optional, Type, TypeVar
from . import internal
from . import meta_value_internal
from .meta_key import MetaKey
from .meta_value import MetaRawValue, MetaValue
from .generated import pushmeta
from .generated.pushmeta import PushmetaLabel

_Self = TypeVar('_Self', bound='Pushmeta')


@internal.tree_model
class Pushmeta(pushmeta.Pushmeta):
    value = meta_value_internal.optional_meta_value_property(pushmeta.Pushmeta.raw_value)

    @classmethod
    def from_value(cls: Type[_Self], key: str, value: Optional[MetaValue | MetaRawValue]) -> _Self:
        return cls.from_children(
            MetaKey.from_value(key),
            meta_value_internal.from_value(value),
        )
