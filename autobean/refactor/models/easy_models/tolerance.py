
from autobean.refactor.models import raw_models
from autobean.refactor.models.raw_models.tolerance import Tilde
from . import internal

internal.token_model(Tilde)


@internal.tree_model
class Tolerance(raw_models.Tolerance):
    number = internal.required_decimal_property(raw_models.Tolerance.raw_number)
