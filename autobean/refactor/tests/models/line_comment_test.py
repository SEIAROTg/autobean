from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestComment:

    @pytest.mark.parametrize(
        'text', [
            ';foo',
            '; foo',
            '; 你好!',
            ';',
            ';"',
            ';""',
            ' ;foo',
            ';foo\n',
            ' ;foo\n',
        ],
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.LineComment)
        assert token.raw_text == text

    @pytest.mark.parametrize(
        'text', [
            '\n;foo',
            '',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.LineComment)
