import datetime
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestDate(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', [
            ('4321-01-23', datetime.date(4321, 1, 23)),
            ('4321-12-01', datetime.date(4321, 12, 1)),
            ('4321-1-3', datetime.date(4321, 1, 3)),
            ('4321/01/23', datetime.date(4321, 1, 23)),
        ],
    )
    def test_parse_success(self, text: str, value: datetime.date) -> None:
        token = self.parser.parse_token(text, models.Date)
        assert token.raw_text == text
        assert token.value == value
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '123-01-23',
            '1234-001-23',
            '1234-01-001',
            '01-01-1234',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.Date)

    def test_set_raw_text(self) -> None:
        token = self.parser.parse_token('4321-01-23', models.Date)
        token.raw_text = '1234-03-21'
        assert token.raw_text == '1234-03-21'
        assert token.value == datetime.date(1234, 3, 21)

    def test_set_raw_text_format(self) -> None:
        token = self.parser.parse_token('4321-01-23', models.Date)
        token.raw_text = '4321/01/23'
        assert token.raw_text == '4321/01/23'
        assert token.value == datetime.date(4321, 1, 23)

    def test_set_value(self) -> None:
        token = self.parser.parse_token('4321-01-23', models.Date)
        token.value = datetime.date(1234, 3, 21)
        assert token.value == datetime.date(1234, 3, 21)
        assert token.raw_text == '1234-03-21'
