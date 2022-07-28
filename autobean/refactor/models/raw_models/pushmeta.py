from . import internal
from .generated.pushmeta import Pushmeta, PushmetaLabel
from .generated.popmeta import Popmeta, PopmetaLabel

internal.token_model(PushmetaLabel)
internal.token_model(PopmetaLabel)
internal.tree_model(Pushmeta)
internal.tree_model(Popmeta)
