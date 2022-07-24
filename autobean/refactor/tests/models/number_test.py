import decimal
from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestNumber(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', [
            ('123', decimal.Decimal(123)),
            ('0', decimal.Decimal(0)),
            ('1.', decimal.Decimal(1)),
            ('000', decimal.Decimal(0)),
            ('010', decimal.Decimal(10)),
            ('123.456', decimal.Decimal('123.456')),
            ('1,234', decimal.Decimal(1234)),
            ('12,345', decimal.Decimal(12345)),
            ('123,456', decimal.Decimal(123456)),
            ('1,234,567', decimal.Decimal(1234567)),
            ('12,345,678', decimal.Decimal(12345678)),
            ('123,456,789', decimal.Decimal(123456789)),
            ('1,234,567.89', decimal.Decimal('1234567.89')),
            ('0,000,000', decimal.Decimal(0)),
            ('1.23456789', decimal.Decimal('1.23456789')),
        ],
    )
    def test_parse_success(self, text: str, value: decimal.Decimal) -> None:
        token = self.raw_parser.parse_token(text, raw_models.Number)
        assert token.raw_text == text
        assert token.value == value
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            '-1',
            '1,2',
            '1,23',
            '1,2345',
            '1234,567',
            '1+2',
            '.1',
            '.',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse_token(text, raw_models.Number)

    @pytest.mark.parametrize(
        'raw_text,new_text,expected_value', [
            ('1234', '1,234', decimal.Decimal(1234)),
            ('1234', '9876.54321', decimal.Decimal('9876.54321')),
        ],
    )
    def test_set_raw_text(self, raw_text: str, new_text: str, expected_value: decimal.Decimal) -> None:
        token = self.raw_parser.parse_token(raw_text, raw_models.Number)
        token.raw_text = new_text
        assert token.raw_text == new_text
        assert token.value == expected_value

    @pytest.mark.parametrize(
        'raw_text,new_value,expected_text', [
            ('1,234', decimal.Decimal(1234), '1234'),
            ('1234', decimal.Decimal('9876.54321'), '9876.54321'),
        ],
    )
    def test_set_value(self, raw_text: str, new_value: decimal.Decimal, expected_text: str) -> None:
        token = self.raw_parser.parse_token(raw_text, raw_models.Number)
        token.value = new_value
        assert token.value == new_value
        assert token.raw_text == expected_text
