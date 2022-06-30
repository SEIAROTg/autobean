from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestBool:

    @pytest.mark.parametrize(
        'text,value', [
            ('TRUE', True),
            ('FALSE', False),
        ],
    )
    def test_parse_success(self, text: str, value: bool, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.Bool)
        assert token.raw_text == text
        assert token.value == value

    @pytest.mark.parametrize(
        'text', [
            'True',
            'False',
            'true',
            'false',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Bool)

    @pytest.mark.parametrize(
        'raw_text,new_text,expected_value', [
            ('FALSE', 'TRUE', True),
            ('TRUE', 'FALSE', False),
        ],
    )
    def test_set_raw_text(self, raw_text: str, new_text: str, expected_value: bool, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(raw_text, raw_models.Bool)
        token.raw_text = new_text
        assert token.raw_text == new_text
        assert token.value == expected_value

    @pytest.mark.parametrize(
        'raw_text,new_value,expected_text', [
            ('FALSE', True, 'TRUE'),
            ('TRUE', False, 'FALSE'),
        ],
    )
    def test_set_value(self, raw_text: str, new_value: bool, expected_text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(raw_text, raw_models.Bool)
        token.value = new_value
        assert token.value == new_value
        assert token.raw_text == expected_text
