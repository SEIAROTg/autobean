import pytest
from lark import exceptions
from autobean.refactor import models
from . import base


class TestComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            ';foo',
            '; foo',
            '; 你好!',
            ';',
            ';"',
            ';""',
        ],
    )
    def test_parse_success_inline(self, text: str) -> None:
        token = self.parser.parse_token(text, models.InlineComment)
        assert token.raw_text == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            ' ;foo',
            ' ;foo\n',
        ],
    )
    def test_parse_success_line(self, text: str) -> None:
        token = self.parser.parse_token(text, models.LineComment)
        assert token.raw_text == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '\n;foo',
            '',
            ' ;foo',
            ' ;foo\n',
            ';foo\n',
        ],
    )
    def test_parse_failure_inline(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.InlineComment)

    @pytest.mark.parametrize(
        'text', [
            '\n;foo',
            '',
            ';foo',
        ],
    )
    def test_parse_failure_line(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.LineComment)

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
