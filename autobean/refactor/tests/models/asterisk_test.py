from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestAsterisk:

    def test_parse_success(self, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('*', raw_models.Asterisk)
        assert token.raw_text == '*'

    @pytest.mark.parametrize(
        'text', [
            'star',
            '**',
            '',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Asterisk)
