import dataclasses
import enum
from typing import Any, Optional


class MetaModel:
    pass


class BlockCommentable:
    pass


class Floating(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


@dataclasses.dataclass(frozen=True)
class field:
    is_label: bool = False
    floating: Optional[Floating] = None
    define_as: Optional[str] = None
    type_alias: Optional[str] = None
    has_circular_dep: bool = False
    is_optional: bool = False
    is_keyword_only: bool = False
    default_value: Any = None
    separators: Optional[tuple[str, ...]] = None
    separators_before: Optional[tuple[str, ...]] = None
    default_indent: Optional[str] = None
