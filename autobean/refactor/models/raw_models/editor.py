from . import base
from . import punctuation


def remove_with_left_whitespace(token_store: base.TokenStore, model: base.RawModel) -> None:
    start = model.first_token
    if start:
        prev = token_store.get_prev(start)
        if isinstance(prev, punctuation.Whitespace):
            start = prev
    end = model.last_token
    token_store.splice((), start, end)
