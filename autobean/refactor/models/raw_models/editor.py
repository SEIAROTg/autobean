from autobean.refactor import token_store as token_store_lib
from . import base
from . import punctuation


def remove_with_left_whitespace(token_store: token_store_lib.TokenStore, model: base.RawModel) -> None:
    start = model.first_token
    if start:
        prev = token_store.get_prev(start)
        if isinstance(prev, punctuation.Whitespace):
            start = prev
    end = model.last_token
    token_store.splice((), start, end)
