from decimal import Decimal


class Policy(dict[str, Decimal]):
    total_weight: Decimal

    def __init__(self) -> None:
        super().__init__()
        self.total_weight = Decimal(0)

    def replace(self, new_policy: 'Policy') -> None:
        super().clear()
        super().update(new_policy)
        self.total_weight = new_policy.total_weight
