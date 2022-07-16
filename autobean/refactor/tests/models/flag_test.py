from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestFlag:

    @pytest.mark.parametrize(
        'text', '!&#?%PSTCURM',
    )
    def test_parse_success(self, text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.Flag)
        assert token.raw_text == text
        assert token.value == text

    @pytest.mark.parametrize(
        'text', [
            'A',
            # * is a valid flag but it's also used elsewhere and should not be matched by this token.
            '*',
            '!!',
            '',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Flag)

    @pytest.mark.parametrize(
        'raw_text,new_text', [
            ('#', '!'),
            ('!', '#'),
        ],
    )
    def test_set_raw_text(self, raw_text: str, new_text: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(raw_text, raw_models.Flag)
        token.raw_text = new_text
        assert token.raw_text == new_text
        assert token.value == new_text

    @pytest.mark.parametrize(
        'raw_text,new_value', [
            ('#', '!'),
            ('!', '#'),
        ],
    )
    def test_set_value(self, raw_text: str, new_value: str, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(raw_text, raw_models.Flag)
        token.value = new_value
        assert token.value == new_value
        assert token.raw_text == new_value
