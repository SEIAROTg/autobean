from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestNewline:

    @pytest.mark.parametrize(
        'text', [
            '\n',
            '\r\n',
            '\r\r\n',
        ],
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.Newline)
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text', [
            '\r',
            '\n ',
            '\n\r',
            '',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Newline)
