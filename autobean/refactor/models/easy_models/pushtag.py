from autobean.refactor.models.raw_models import pushtag
from autobean.refactor.models.raw_models.pushtag import PushtagLabel, PoptagLabel
from . import internal

internal.token_model(PushtagLabel)
internal.token_model(PoptagLabel)


@internal.tree_model
class Pushtag(pushtag.Pushtag):
    tag = internal.required_string_property(pushtag.Pushtag.raw_tag)


@internal.tree_model
class Poptag(pushtag.Poptag):
    tag = internal.required_string_property(pushtag.Poptag.raw_tag)
