import decimal
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
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
        amount = self._parser.parse(text, raw_models.Amount)
        assert amount.first_token is amount.raw_number_expr.first_token
        assert amount.raw_number_expr.value == number
        assert amount.raw_currency.value == currency
        assert amount.last_token is amount.raw_currency
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
            self._parser.parse(text, raw_models.Amount)

    def test_set_raw_number_expr(self) -> None:
        amount = self._parser.parse('100.00  USD', raw_models.Amount)
        new_number_expr = self._parser.parse('(100.00 + 20.00)', raw_models.NumberExpr)
        amount.raw_number_expr = new_number_expr
        assert amount.raw_number_expr is new_number_expr
        assert self.print_model(amount) == '(100.00 + 20.00)  USD'

    def test_set_raw_currency(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00)  USD', easy_models.Amount)
        new_currency = raw_models.Currency.from_value('EUR')
        amount.raw_currency = new_currency
        assert amount.raw_currency is new_currency
        assert self.print_model(amount) == '(100.00 + 20.00)  EUR'

    def test_set_number(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00)  USD', easy_models.Amount)
        assert amount.number == decimal.Decimal('120.00')
        amount.number = decimal.Decimal('-12.34')
        assert amount.number == decimal.Decimal('-12.34')
        assert self.print_model(amount) == '-12.34  USD'

    def test_set_currency(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00)  USD', easy_models.Amount)
        assert amount.currency == 'USD'
        amount.currency = 'EUR'
        assert amount.currency == 'EUR'
        assert self.print_model(amount) == '(100.00 + 20.00)  EUR'
