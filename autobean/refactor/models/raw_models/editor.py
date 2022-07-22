from . import base
from . import punctuation


def remove_towards_left(instance: base.RawTreeModel, value: base.RawTokenModel | base.RawTreeModel) -> None:
    start = value.first_token
    if start:
        prev = instance.token_store.get_prev(start)
        if isinstance(prev, punctuation.Whitespace):
            start = prev
    end = value.last_token
    instance.token_store.splice((), start, end)
