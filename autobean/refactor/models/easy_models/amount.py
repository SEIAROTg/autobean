from autobean.refactor.models.raw_models import amount
from . import internal


@internal.tree_model
class Amount(amount.Amount):
    number = internal.required_number_expr_property(amount.Amount.raw_number_expr)
    currency = internal.required_string_property(amount.Amount.raw_currency)
