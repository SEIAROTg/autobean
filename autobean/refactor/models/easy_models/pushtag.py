from autobean.refactor.models.raw_models import pushtag
from . import internal


class Pushtag(pushtag.Pushtag):
    tag = internal.required_string_property(pushtag.Pushtag.raw_tag)


class Poptag(pushtag.Poptag):
    tag = internal.required_string_property(pushtag.Poptag.raw_tag)
