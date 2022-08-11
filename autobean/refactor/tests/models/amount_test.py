import decimal
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestAmount(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,number,currency', [
            ('100.00 USD', decimal.Decimal('100.00'), 'USD'),
            ('100.00USD', decimal.Decimal('100.00'), 'USD'),
            ('100.00 \t USD', decimal.Decimal('100.00'), 'USD'),
            ('-100.00 + 20 USD', decimal.Decimal('-80.00'), 'USD'),
            ('(10+20) USD', decimal.Decimal('30.00'), 'USD'),
        ],
    )
    def test_parse_success(self, text: str, number: decimal.Decimal, currency: str) -> None:
        amount = self.parser.parse_inline(text, models.Amount)
        assert amount.raw_number.value == number
        assert amount.raw_currency.value == currency
        assert self.print_model(amount) == text
        self.check_deepcopy_tree(amount)
        self.check_reattach_tree(amount)

    @pytest.mark.parametrize(
        'text', [
            '100.00',
            'USD',
            '10+ USD',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_inline(text, models.Amount)

    def test_set_raw_number(self) -> None:
        amount = self.parser.parse_inline('100.00  USD', models.Amount)
        new_number = self.parser.parse_inline('(100.00 + 20.00)', models.NumberExpr)
        amount.raw_number = new_number
        assert amount.raw_number is new_number
        assert self.print_model(amount) == '(100.00 + 20.00)  USD'

    def test_set_raw_currency(self) -> None:
        amount = self.parser.parse_inline('(100.00 + 20.00)  USD', models.Amount)
        new_currency = models.Currency.from_value('EUR')
        amount.raw_currency = new_currency
        assert amount.raw_currency is new_currency
        assert self.print_model(amount) == '(100.00 + 20.00)  EUR'

    def test_set_number(self) -> None:
        amount = self.parser.parse_inline('(100.00 + 20.00)  USD', models.Amount)
        assert amount.number == decimal.Decimal('120.00')
        amount.number = decimal.Decimal('-12.34')
        assert amount.number == decimal.Decimal('-12.34')
        assert self.print_model(amount) == '-12.34  USD'

    def test_set_currency(self) -> None:
        amount = self.parser.parse_inline('(100.00 + 20.00)  USD', models.Amount)
        assert amount.currency == 'USD'
        amount.currency = 'EUR'
        assert amount.currency == 'EUR'
        assert self.print_model(amount) == '(100.00 + 20.00)  EUR'

    def test_from_children(self) -> None:
        number = models.NumberExpr.from_value(decimal.Decimal('100.00'))
        currency = models.Currency.from_value('USD')
        amount = models.Amount.from_children(number, currency)
        assert amount.raw_number is number
        assert amount.raw_currency is currency
        assert self.print_model(amount) == '100.00 USD' 
        self.check_consistency(amount)

    def test_from_value(self) -> None:
        amount = models.Amount.from_value(decimal.Decimal('100.00'), 'USD')
        assert amount.raw_number.value == decimal.Decimal('100.00')
        assert amount.raw_currency.value == 'USD'
        assert self.print_model(amount) == '100.00 USD'
        self.check_consistency(amount)
