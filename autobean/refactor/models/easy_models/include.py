from autobean.refactor.models.raw_models import include
from . import internal


class Include(include.Include):
    filename = internal.required_string_property(include.Include.raw_filename)
