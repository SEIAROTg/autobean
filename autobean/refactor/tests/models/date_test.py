import datetime
from lark import exceptions
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor.models import raw_models


class TestDate:

    @pytest.mark.parametrize(
        'text,value', [
            ('4321-01-23', datetime.date(4321, 1, 23)),
            ('4321-12-01', datetime.date(4321, 12, 1)),
            ('4321-1-3', datetime.date(4321, 1, 3)),
            ('4321/01/23', datetime.date(4321, 1, 23)),
        ],
    )
    def test_parse_success(self, text: str, value: datetime.date, parser: parser_lib.Parser) -> None:
        token = parser.parse_token(text, raw_models.Date)
        assert token.raw_text == text
        assert token.value == value

    @pytest.mark.parametrize(
        'text', [
            '123-01-23',
            '1234-001-23',
            '1234-01-001',
            '01-01-1234',
        ],
    )
    def test_parse_failure(self, text: str, parser: parser_lib.Parser) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            parser.parse_token(text, raw_models.Date)

    def test_set_raw_text(self, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('4321-01-23', raw_models.Date)
        token.raw_text = '1234-03-21'
        assert token.raw_text == '1234-03-21'
        assert token.value == datetime.date(1234, 3, 21)

    def test_set_raw_text_format(self, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('4321-01-23', raw_models.Date)
        token.raw_text = '4321/01/23'
        assert token.raw_text == '4321/01/23'
        assert token.value == datetime.date(4321, 1, 23)

    def test_set_value(self, parser: parser_lib.Parser) -> None:
        token = parser.parse_token('4321-01-23', raw_models.Date)
        token.value = datetime.date(1234, 3, 21)
        assert token.value == datetime.date(1234, 3, 21)
        assert token.raw_text == '1234-03-21'
