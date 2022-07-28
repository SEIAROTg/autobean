from . import internal
from .generated.query import Query, QueryLabel

internal.tree_model(Query)
internal.token_model(QueryLabel)
