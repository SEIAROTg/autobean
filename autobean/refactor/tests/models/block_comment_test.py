import pytest
from lark import exceptions
from autobean.refactor import models
from .. import base

_PARSE_TESTCASES = [
    (';foo', '', 'foo'),
    ('; foo', '', 'foo'),
    (';', '', ''),
    ('  ;', '  ', ''),
    (';foo\n;bar', '', 'foo\nbar'),
    (';foo\r\n;bar', '', 'foo\r\nbar'),
    ('\t; foo', '\t', 'foo'),
    ('\t; foo\n  ;bar', '\t', 'foo\nbar'),
]
_FORMAT_TESTCASES = [
    ('; foo', '', 'foo'),
    (';', '', ''),
    ('; foo\n; bar', '', 'foo\nbar'),
    ('  ; foo', '  ', 'foo'),
    ('  ; foo\n  ; bar', '  ', 'foo\nbar'),
    ('\t; foo\r\n\t; bar', '\t', 'foo\r\nbar'),
]


class TestBlockComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,indent,value', _PARSE_TESTCASES,
    )
    def test_parse_success(self, text: str, indent: str, value: str) -> None:
        token = self.parser.parse_token(text, models.BlockComment)
        assert token.raw_text == text
        assert token.indent == indent
        assert token.value == value
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '',
            ';foo\n',
            ';foo;bar\n',
            '  ; foo\n;bar',
            '; foo\n  ;bar',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.BlockComment)

    @pytest.mark.parametrize(
        'text,indent,value', _PARSE_TESTCASES,
    )
    def test_from_raw_text(self, text: str, indent: str, value: str) -> None:
        comment = models.BlockComment.from_raw_text(text)
        assert comment.raw_text == text
        assert comment.indent == indent
        assert comment.value == value

    @pytest.mark.parametrize(
        'text,indent,value', _FORMAT_TESTCASES,
    )
    def test_from_value(self, text: str, indent: str, value: str) -> None:
        comment = models.BlockComment.from_value(value, indent=indent)
        assert comment.raw_text == text
        assert comment.indent == indent
        assert comment.value == value

    @pytest.mark.parametrize(
        'text,indent,value', _FORMAT_TESTCASES
    )
    def test_set_indent_value(self, text: str, indent: str, value: str) -> None:
        comment = models.BlockComment.from_raw_text(' ; foo')
        comment.indent = indent
        comment.value = value
        assert comment.raw_text == text
        assert comment.indent == indent
        assert comment.value == value
