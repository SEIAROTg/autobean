from . import internal
from .generated.pushtag import Pushtag, PushtagLabel
from .generated.poptag import Poptag, PoptagLabel

internal.tree_model(Pushtag)
internal.tree_model(Poptag)
internal.token_model(PushtagLabel)
internal.token_model(PoptagLabel)
