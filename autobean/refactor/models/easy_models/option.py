from autobean.refactor.models.raw_models import option
from . import internal


class Option(option.Option):
    key = internal.required_string_property(option.Option.raw_key)
    value = internal.required_string_property(option.Option.raw_value)
