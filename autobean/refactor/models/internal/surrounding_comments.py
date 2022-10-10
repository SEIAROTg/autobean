from typing import Callable, Optional
from . import fields
from .placeholder import Placeholder
from .. import base
from ..spacing import Newline
from ..block_comment import BlockComment


def _take_ignored(
        token: Optional[base.RawTokenModel],
        succ: Callable[[base.RawTokenModel], Optional[base.RawTokenModel]],
        ignored: list[base.RawTokenModel],
) -> Optional[base.RawTokenModel]:
    while isinstance(token, Placeholder):
        ignored.append(token)
        token = succ(token)
    return token


def _claim_comment(
    current: Optional[BlockComment],
    token_store: base.TokenStore,
    start: base.RawTokenModel,
    *,
    backwards: bool,
    ignore_if_already_claimed: bool,
) -> Optional[BlockComment]:
    if current is not None:
        return current

    ignored: list[base.RawTokenModel] = []
    if backwards:
        succ = token_store.get_prev
    else:
        succ = token_store.get_next

    first = succ(start)
    if first is None:
        return None

    newline = _take_ignored(first, succ, ignored)
    if not isinstance(newline, Newline):
        return None
    comment = _take_ignored(succ(newline), succ, ignored)
    if not isinstance(comment, BlockComment):
        return None

    if comment.claimed:
        if ignore_if_already_claimed:
            return None
        raise ValueError('Comment already claimed.')
    comment.claimed = True
    if ignored:
        if backwards:
            token_store.splice(
                [*reversed(ignored), comment, newline], comment, first)
        else:
            token_store.splice(
                [newline, comment, *ignored], first, comment)
    return comment


class SurroundingCommentsMixin(base.RawTreeModel):
    _leading_comment = fields.optional_right_field[BlockComment](separators=(Newline.from_default(),))
    _trailing_comment = fields.optional_left_field[BlockComment](separators=(Newline.from_default(),))

    def claim_leading_comment(self, *, ignore_if_already_claimed: bool = False) -> Optional[BlockComment]:
        self._leading_comment = _claim_comment(
            self._leading_comment,
            self.token_store,
            self.first_token,
            backwards=True,
            ignore_if_already_claimed=ignore_if_already_claimed)
        return self._leading_comment

    def unclaim_leading_comment(self) -> Optional[BlockComment]:
        current = self._leading_comment
        if current is not None:
            current.claimed = False
            self._leading_comment = None
        return current

    def claim_trailing_comment(self, *, ignore_if_already_claimed: bool = False) -> Optional[BlockComment]:
        self._trailing_comment = _claim_comment(
            self._trailing_comment,
            self.token_store,
            self.last_token,
            backwards=False,
            ignore_if_already_claimed=ignore_if_already_claimed)
        return self._trailing_comment

    def unclaim_trailing_comment(self) -> Optional[BlockComment]:
        current = self._trailing_comment
        if current is not None:
            current.claimed = False
            self._trailing_comment = None
        return current
