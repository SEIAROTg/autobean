from . import internal
from .generated import unit_cost, total_cost
from .generated.unit_cost import LeftBrace, RightBrace
from .generated.total_cost import DblLeftBrace, DblRightBrace


@internal.tree_model
class UnitCost(unit_cost.UnitCost):
    def into_total_cost(self) -> 'TotalCost':
        dbl_left_brace = DblLeftBrace.from_default()
        dbl_right_brace = DblRightBrace.from_default()
        self.token_store.replace(self._left_brace, dbl_left_brace)
        self.token_store.replace(self._right_brace, dbl_right_brace)
        return TotalCost(self.token_store, dbl_left_brace, self._components, dbl_right_brace)


@internal.tree_model
class TotalCost(total_cost.TotalCost):
    def into_unit_cost(self) -> UnitCost:
        left_brace = LeftBrace.from_default()
        right_brace = RightBrace.from_default()
        self.token_store.replace(self._dbl_left_brace, left_brace)
        self.token_store.replace(self._dbl_right_brace, right_brace)
        return UnitCost(self.token_store, left_brace, self._components, right_brace)
