import decimal
from typing import Type, TypeVar
from . import internal
from .generated import tolerance
from .generated.tolerance import Tilde

_Self = TypeVar('_Self', bound='Tolerance')


@internal.tree_model
class Tolerance(tolerance.Tolerance, internal.RWValue[decimal.Decimal]):

    @property
    def value(self) -> decimal.Decimal:
        return self.raw_number.value

    @value.setter
    def value(self, value: decimal.Decimal) -> None:
        self.raw_number.value = value

    @classmethod
    def from_value(
            cls: Type[_Self],
            number: decimal.Decimal,
    ) -> _Self:
        return super().from_value(number)
