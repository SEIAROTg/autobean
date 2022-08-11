from autobean.refactor import models
from . import base


class TestComment(base.BaseTestModel):

    def test_all_comments_in_file(self) -> None:
        text = '''\
; comment at the beginning

include "foo.bean"

; comment in the middle

include "bar.bean"

; comment at the end
'''
        file = self.parser.parse(text, models.File)
        assert self.print_model(file) == text

    def test_model_end_inline_comment_in_model(self) -> None:
        text = '2000-01-01 close Assets:Foo  ; comment'
        close = self.parser.parse(text, models.Close)
        assert self.print_model(close) == text
