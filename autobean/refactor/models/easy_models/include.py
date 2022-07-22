from autobean.refactor.models.raw_models import include
from autobean.refactor.models.raw_models.include import IncludeLabel
from . import internal

internal.token_model(IncludeLabel)


@internal.tree_model
class Include(include.Include):
    filename = internal.required_string_property(include.Include.raw_filename)
