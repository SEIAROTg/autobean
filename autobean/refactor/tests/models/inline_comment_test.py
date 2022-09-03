import pytest
from lark import exceptions
from autobean.refactor import models
from . import base


class TestInlineComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', [
            (';foo', 'foo'),
            ('; foo', 'foo'),
            ('; 你好!', '你好!'),
            (';', ''),
            (';"', '"'),
            (';""', '""'),
        ],
    )
    def test_parse_success(self, text: str, value: str) -> None:
        token = self.parser.parse_token(text, models.InlineComment)
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
            self.parser.parse_token(text, models.InlineComment)

    @pytest.mark.parametrize(
        'text,value', [
            ('; foo', 'foo'),
            (';', ''),
        ],
    )
    def test_from_value(self, text: str, value: str) -> None:
        comment = models.InlineComment.from_value(value)
        assert comment.value == value
        assert comment.raw_text == text

    @pytest.mark.parametrize(
        'text,value', [
            ('; foo', 'foo'),
            (';', ''),
        ],
    )
    def test_set_value(self, text: str, value: str) -> None:
        comment = models.InlineComment.from_value('bar')
        comment.value = value
        assert comment.value == value
        assert comment.raw_text == text
