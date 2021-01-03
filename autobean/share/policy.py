from decimal import Decimal


class Policy(dict):
    total_weight: Decimal

    def replace(self, new_policy):
        super().clear()
        super().update(new_policy)
        self.total_weight = new_policy.total_weight
