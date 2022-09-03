import itertools
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base

# (text, value)
_ESCAPE_TEST_CASES_COMMON = [
    ('""', ''),
    ('"foo"', 'foo'),
    ('"\'\'"', "''"),
    (r'"\""', '"'),
    (r'"\\"', '\\'),
    (r'"你好"', '你好'),
    (r'"\\\\n"', '\\\\n'),
]
_UNESCAPE_TEST_CASE_LOSS = [
    (r'"\u4f60\u597d"', 'u4f60u597d'),
]
_ESCAPE_TEST_CASES_CONSERVATIVE = [
    ('"\n"', '\n'),
    ('"\t"', '\t'),
    ('"multiple\nlines"', 'multiple\nlines'),
]
_ESCAPE_TEST_CASES_AGGRESSIVE = [
    (r'"\n"', '\n'),
    (r'"\t"', '\t'),
    (r'"multiple\nlines"', 'multiple\nlines'),
]


class TestEscapedString(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _UNESCAPE_TEST_CASE_LOSS,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_parse_success(self, text: str, value: str) -> None:
        token = self.parser.parse_token(text, models.EscapedString)
        assert token.value == value
        assert token.raw_text == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            'foo',
            "'foo'",
            '"foo',
            'foo"',
            '"""',
            '',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.EscapedString)

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _UNESCAPE_TEST_CASE_LOSS,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_set_raw_text(self, text: str, value: str) -> None:
        token = self.parser.parse_token('"dummy"', models.EscapedString)
        token.raw_text = text
        assert token.value == value
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
        ),
    )
    def test_set_value(self, text: str, value: str) -> None:
        token = self.parser.parse_token('"dummy"', models.EscapedString)
        token.value = value
        assert token.value == value
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _UNESCAPE_TEST_CASE_LOSS,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_unesacpe(self, text: str, value: str) -> None:
        actual_value = models.EscapedString.unescape(text[1:-1])
        assert actual_value == value

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
        ),
    )
    def test_esacpe_conservative(self, text: str, value: str) -> None:
        actual_text = models.EscapedString.escape(value)
        assert actual_text == text[1:-1]

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_esacpe_aggressive(self, text: str, value: str) -> None:
        actual_text = models.EscapedString.escape(value, aggressive=True)
        assert actual_text == text[1:-1]
