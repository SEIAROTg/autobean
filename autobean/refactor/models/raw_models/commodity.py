from . import internal
from .generated.commodity import Commodity, CommodityLabel

internal.tree_model(Commodity)
internal.token_model(CommodityLabel)
