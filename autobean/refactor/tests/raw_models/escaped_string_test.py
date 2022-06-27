import itertools
from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models

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


class TestEscapedString:

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _UNESCAPE_TEST_CASE_LOSS,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_parse_success(self, text: str, value: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.EscapedString)
        assert token.value == value
        assert token.raw_text == text

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
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.EscapedString)

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _UNESCAPE_TEST_CASE_LOSS,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_set_raw_text(self, text: str, value: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('"dummy"', raw_models.EscapedString)
        token.raw_text = text
        assert token.value == value
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
        ),
    )
    def test_set_value(self, text: str, value: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('"dummy"', raw_models.EscapedString)
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
        actual_value = raw_models.EscapedString.unescape(text[1:-1])
        assert actual_value == value

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_CONSERVATIVE,
        ),
    )
    def test_esacpe_conservative(self, text: str, value: str) -> None:
        actual_text = raw_models.EscapedString.escape(value)
        assert actual_text == text[1:-1]

    @pytest.mark.parametrize(
        'text,value', itertools.chain(
            _ESCAPE_TEST_CASES_COMMON,
            _ESCAPE_TEST_CASES_AGGRESSIVE,
        ),
    )
    def test_esacpe_aggressive(self, text: str, value: str) -> None:
        actual_text = raw_models.EscapedString.escape(value, aggressive=True)
        assert actual_text == text[1:-1]
