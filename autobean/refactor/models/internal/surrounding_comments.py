from . import fields
from .. import base
from ..spacing import Newline
from ..block_comment import BlockComment


class SurroundingCommentsMixin(base.RawTreeModel):
    _leading_comment = fields.optional_right_field[BlockComment](separators=(Newline.from_default(),))
    _trailing_comment = fields.optional_left_field[BlockComment](separators=(Newline.from_default(),))

    def claim_leading_comment(self, comment: BlockComment) -> None:
        existing_comment = self._leading_comment.inner
        if existing_comment is comment:
            return
        if comment.claimed:
            raise ValueError('Comment already claimed.')
        if existing_comment is not None:
            raise ValueError('Leading comment already exists.')
        if comment.token_store is not self.token_store:
            raise ValueError('Comment does not belong to the same context.')
        comment.claimed = True
        self._leading_comment.inner = comment

    def unclaim_leading_comment(self) -> None:
        existing_comment = self._leading_comment.inner
        if existing_comment is None:
            return
        existing_comment.claimed = False
        self._leading_comment.inner = None

    def claim_trailing_comment(self, comment: BlockComment) -> None:
        existing_comment = self._trailing_comment.inner
        if existing_comment is comment:
            return
        if comment.claimed:
            raise ValueError('Comment already claimed.')
        if existing_comment is not None:
            raise ValueError('Trailing comment already exists.')
        if comment.token_store is not self.token_store:
            raise ValueError('Comment does not belong to the same context.')
        comment.claimed = True
        self._trailing_comment.inner = comment

    def unclaim_trailing_comment(self) -> None:
        existing_comment = self._trailing_comment.inner
        if existing_comment is None:
            return
        existing_comment.claimed = False
        self._trailing_comment.inner = None
