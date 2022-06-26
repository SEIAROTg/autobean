from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestWhitespace:

    @pytest.mark.parametrize(
        'text', [
            ' ',
            '    ',
            '\t',
            '\t\t\t\t',
            ' \t \t',
        ],
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.Whitespace)
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text', [
            ''
            '\n',
            '\u00a0',
            '\u2000',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Whitespace)
