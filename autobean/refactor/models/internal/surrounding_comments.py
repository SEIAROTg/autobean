from typing import Callable, Optional
from . import fields
from .placeholder import Placeholder
from .. import base, internal
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
    maybe_comment: internal.Maybe[BlockComment],
    start: base.RawTokenModel,
    *,
    backwards: bool,
    ignore_if_already_claimed: bool,
) -> Optional[BlockComment]:
    if maybe_comment.inner is not None:
        return maybe_comment.inner

    ignored: list[base.RawTokenModel] = []
    if backwards:
        succ = maybe_comment.token_store.get_prev
    else:
        succ = maybe_comment.token_store.get_next

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
    maybe_comment.inner = comment
    if ignored:
        if backwards:
            maybe_comment.token_store.splice(
                [*reversed(ignored), comment, newline], comment, first)
        else:
            maybe_comment.token_store.splice(
                [newline, comment, *ignored], first, comment)
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
            backwards=True,
            ignore_if_already_claimed=ignore_if_already_claimed)

    def unclaim_leading_comment(self) -> Optional[BlockComment]:
        return _unclaim_comment(self._leading_comment)

    def claim_trailing_comment(self, *, ignore_if_already_claimed: bool = False) -> Optional[BlockComment]:
        return _claim_comment(
            self._trailing_comment,
            self.last_token,
            backwards=False,
            ignore_if_already_claimed=ignore_if_already_claimed)

    def unclaim_trailing_comment(self) -> Optional[BlockComment]:
        return _unclaim_comment(self._trailing_comment)
