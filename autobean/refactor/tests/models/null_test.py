from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestNull:

    def test_parse_success(self, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('NULL', raw_models.Null)
        assert token.raw_text == 'NULL'

    @pytest.mark.parametrize(
        'text', [
            'Null',
            'None',
            'null',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Null)
