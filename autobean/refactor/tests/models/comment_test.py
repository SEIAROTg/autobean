import pytest
from lark import exceptions
from autobean.refactor import models
from . import base


class TestComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text, value', [
            (';foo', 'foo'),
            ('; foo', 'foo'),
            ('; 你好!', '你好!'),
            (';', ''),
            (';"', '"'),
            (';""', '""'),
        ],
    )
    def test_parse_success(self, text: str, value: str) -> None:
        token = self.parser.parse_token(text, models.Comment)
        assert token.raw_text == text
        assert token.value == value
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '\n;foo',
            '',
            ' ;foo',
            ' ;foo\n',
            ';foo\n',
            ' ;foo',
            ' ;foo\n',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.Comment)

    def test_from_value(self) -> None:
        comment = models.Comment.from_value('foo')
        assert comment.value == 'foo'
        assert comment.raw_text == '; foo'

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
