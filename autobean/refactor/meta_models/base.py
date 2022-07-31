import dataclasses
import enum
from typing import Optional


class MetaModel:
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
