from typing import Callable, Optional
from . import fields
from .. import base, internal
from ..spacing import Newline
from ..block_comment import BlockComment


def _claim_comment(
    maybe_comment: internal.Maybe[BlockComment],
    start: base.RawTokenModel,
    succ: Callable[[base.RawTokenModel], Optional[base.RawTokenModel]],
    ignore_if_already_claimed: bool,
) -> Optional[BlockComment]:
    if maybe_comment.inner is not None:
        return maybe_comment.inner
    newline = succ(start)
    if not isinstance(newline, Newline):
        return None
    comment = succ(newline)
    if not isinstance(comment, BlockComment):
        return None
    if comment.claimed:
        if ignore_if_already_claimed:
            return None
        raise ValueError('Comment already claimed.')
    comment.claimed = True
    maybe_comment.inner = comment
    return comment


def _unclaim_comment(maybe_comment: internal.Maybe[BlockComment]) -> Optional[BlockComment]:
    existing_comment = maybe_comment.inner
    if existing_comment is None:
        return None
    existing_comment.claimed = False
    maybe_comment.inner = None
    return existing_comment


class SurroundingCommentsMixin(base.RawTreeModel):
    _leading_comment = fields.optional_right_field[BlockComment](separators=(Newline.from_default(),))
    _trailing_comment = fields.optional_left_field[BlockComment](separators=(Newline.from_default(),))

    def claim_leading_comment(self, *, ignore_if_already_claimed: bool = False) -> Optional[BlockComment]:
        return _claim_comment(
            self._leading_comment,
            self.first_token,
            self.token_store.get_prev,
            ignore_if_already_claimed=ignore_if_already_claimed)

    def unclaim_leading_comment(self) -> Optional[BlockComment]:
        return _unclaim_comment(self._leading_comment)

    def claim_trailing_comment(self, *, ignore_if_already_claimed: bool = False) -> Optional[BlockComment]:
        return _claim_comment(
            self._trailing_comment,
            self.last_token,
            self.token_store.get_next,
            ignore_if_already_claimed=ignore_if_already_claimed)

    def unclaim_trailing_comment(self) -> Optional[BlockComment]:
        return _unclaim_comment(self._trailing_comment)
