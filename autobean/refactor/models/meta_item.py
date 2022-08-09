from .generated.note import *
from typing import Optional, Type, TypeVar
from . import internal
from . import meta_value_internal
from .meta_key import MetaKey
from .meta_value import MetaRawValue, MetaValue
from .punctuation import Indent
from .generated import meta_item

_Self = TypeVar('_Self', bound='MetaItem')


@internal.tree_model
class MetaItem(meta_item.MetaItem):
    value = meta_value_internal.optional_meta_value_property(meta_item.MetaItem.raw_value)

    @classmethod
    def from_value(
            cls: Type[_Self],
            key: str,
            value: Optional[MetaValue | MetaRawValue],
            *,
            indent: str = '    ') -> _Self:
        return cls.from_children(
            Indent.from_value(indent),
            MetaKey.from_value(key),
            meta_value_internal.from_value(value),
        )
