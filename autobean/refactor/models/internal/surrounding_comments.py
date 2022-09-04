from . import fields
from .. import base
from ..spacing import Newline
from ..block_comment import BlockComment


class SurroundingCommentsMixin(base.RawTreeModel):
    _leading_comment = fields.optional_right_field[BlockComment](separators=(Newline.from_default(),))
    _trailing_comment = fields.optional_left_field[BlockComment](separators=(Newline.from_default(),))
