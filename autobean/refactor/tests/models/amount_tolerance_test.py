import decimal
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base

_D = decimal.Decimal


class TestAmount(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,number,tolerance,currency', [
            ('100.00 USD', _D('100.00'), None, 'USD'),
            ('100.00USD', _D('100.00'), None, 'USD'),
            ('100.00 ~ 0.01 USD', _D('100.00'), _D('0.01'), 'USD'),
            ('100.00~0.01USD', _D('100.00'), _D('0.01'), 'USD'),
            ('100.00 + 2.00 ~ 0.01 * 2 USD', _D('102.00'), _D('0.02'), 'USD'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            number: decimal.Decimal,
            tolerance: Optional[decimal.Decimal],
            currency: str,
    ) -> None:
        amount = self._parser.parse(text, easy_models.AmountTolerance)
        assert amount.first_token is amount.raw_number.first_token
        assert amount.raw_number.value == number
        assert amount.number == number
        if amount.raw_tolerance is None:
            assert tolerance is None
        else:
            assert amount.raw_tolerance.value == tolerance
        assert amount.tolerance == tolerance
        assert amount.raw_currency.value == currency
        assert amount.currency == currency
        assert amount.last_token is amount.raw_currency
        self.check_deepcopy_tree(amount)
        self.check_reattach_tree(amount)

    @pytest.mark.parametrize(
        'text', [
            '100.00',
            'USD',
            '10+ USD',
            '100.00 ~~ 0.01 USD',
            '100.00 ~ 0.01 ~ 0.01 USD',
            '100.00 USD ~ 0.01',
            '100.00 USD ~ 0.01 USD',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.AmountTolerance)

    def test_set_raw_number(self) -> None:
        amount = self._parser.parse('100.00 ~ 0.01  USD', raw_models.AmountTolerance)
        new_number = self._parser.parse('(100.00 + 20.00)', raw_models.NumberExpr)
        amount.raw_number = new_number
        assert amount.raw_number is new_number
        assert self.print_model(amount) == '(100.00 + 20.00) ~ 0.01  USD'

    @pytest.mark.parametrize(
        'text,raw_tolerance,expected', [
            ('100.00  USD', None, '100.00  USD'),
            ('100.00  USD', raw_models.NumberExpr.from_value(_D('0.01')), '100.00 ~ 0.01  USD'),
            ('100.00 ~ 0.01  USD', raw_models.NumberExpr.from_value(_D('0.02')), '100.00 ~ 0.02  USD'),
            ('100.00 ~ 0.01  USD', None, '100.00  USD'),
        ],
    )
    def test_set_raw_tolerance(self, text: str, raw_tolerance: Optional[raw_models.NumberExpr], expected: str) -> None:
        amount = self._parser.parse(text, easy_models.AmountTolerance)
        amount.raw_tolerance = raw_tolerance
        assert amount.raw_tolerance is raw_tolerance
        assert self.print_model(amount) == expected
        self.check_consistency(amount)

    def test_set_raw_currency(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00) ~ 0.01  USD', raw_models.AmountTolerance)
        new_currency = raw_models.Currency.from_value('EUR')
        amount.raw_currency = new_currency
        assert amount.raw_currency is new_currency
        assert self.print_model(amount) == '(100.00 + 20.00) ~ 0.01  EUR'

    def test_set_number(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00) ~ 0.01  USD', easy_models.AmountTolerance)
        assert amount.number == _D('120.00')
        amount.number = _D('-12.34')
        assert amount.number == _D('-12.34')
        assert self.print_model(amount) == '-12.34 ~ 0.01  USD'

    @pytest.mark.parametrize(
        'text,tolerance,expected', [
            ('100.00  USD', _D('0.01'), '100.00 ~ 0.01  USD'),
            ('100.00 ~ 0.01  USD', _D('0.02'), '100.00 ~ 0.02  USD'),
            ('100.00 ~ 0.01  USD', None, '100.00  USD'),
        ],
    )
    def test_set_tolerance(self, text: str, tolerance: Optional[decimal.Decimal], expected: str) -> None:
        amount = self._parser.parse(text, easy_models.AmountTolerance)
        amount.tolerance = tolerance
        assert amount.tolerance == tolerance
        assert self.print_model(amount) == expected
        self.check_consistency(amount)

    def test_set_currency(self) -> None:
        amount = self._parser.parse('(100.00 + 20.00) ~ 0.01  USD', easy_models.AmountTolerance)
        assert amount.currency == 'USD'
        amount.currency = 'EUR'
        assert amount.currency == 'EUR'
        assert self.print_model(amount) == '(100.00 + 20.00) ~ 0.01  EUR'

    def test_from_children_with_tolerance(self) -> None:
        number = raw_models.NumberExpr.from_value(_D('100.00'))
        tolerance = raw_models.NumberExpr.from_value(_D('0.01'))
        currency = raw_models.Currency.from_value('USD')
        amount = raw_models.AmountTolerance.from_children(number, tolerance, currency)
        assert amount.raw_number is number
        assert amount.raw_tolerance is tolerance
        assert amount.raw_currency is currency
        assert self.print_model(amount) == '100.00 ~ 0.01 USD' 
        self.check_consistency(amount)

    def test_from_children_without_tolerance(self) -> None:
        number = raw_models.NumberExpr.from_value(_D('100.00'))
        currency = raw_models.Currency.from_value('USD')
        amount = raw_models.AmountTolerance.from_children(number, None, currency)
        assert amount.raw_number is number
        assert amount.raw_tolerance is None
        assert amount.raw_currency is currency
        assert self.print_model(amount) == '100.00 USD' 
        self.check_consistency(amount)

    def test_from_value_with_tolerance(self) -> None:
        amount = easy_models.AmountTolerance.from_value(_D('100.00'), _D('0.01'), 'USD')
        assert amount.raw_number.value == _D('100.00')
        assert amount.raw_tolerance and amount.raw_tolerance.value == _D('0.01')
        assert amount.raw_currency.value == 'USD'
        assert self.print_model(amount) == '100.00 ~ 0.01 USD'
        self.check_consistency(amount)

    def test_from_value_without_tolerance(self) -> None:
        amount = easy_models.AmountTolerance.from_value(_D('100.00'), None, 'USD')
        assert amount.raw_number.value == _D('100.00')
        assert amount.raw_tolerance is None
        assert amount.raw_currency.value == 'USD'
        assert self.print_model(amount) == '100.00 USD'
        self.check_consistency(amount)
