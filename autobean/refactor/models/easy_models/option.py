from autobean.refactor.models.raw_models import option
from autobean.refactor.models.raw_models.option import OptionLabel
from . import internal

internal.token_model(OptionLabel)


@internal.tree_model
class Option(option.Option):
    key = internal.required_string_property(option.Option.raw_key)
    value = internal.required_string_property(option.Option.raw_value)
