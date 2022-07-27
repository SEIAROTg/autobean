import datetime
import decimal
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base

_D = decimal.Decimal


class Testbalance(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,number,tolerance,currency', [
            ('2000-01-01 balance Assets:Foo 100.00 USD', _D('100.00'), None, 'USD'),
            ('2000-01-01 balance Assets:Foo 100.00USD', _D('100.00'), None, 'USD'),
            ('2000-01-01 balance Assets:Foo 100.00 ~ 0.01 USD', _D('100.00'), _D('0.01'), 'USD'),
            ('2000-01-01 balance Assets:Foo 100.00~0.01USD', _D('100.00'), _D('0.01'), 'USD'),
            ('2000-01-01 balance Assets:Foo 100.00 + 2.00 ~ 0.01 * 2 USD', _D('102.00'), _D('0.02'), 'USD'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            number: decimal.Decimal,
            tolerance: Optional[decimal.Decimal],
            currency: str,
    ) -> None:
        date = datetime.date(2000, 1, 1)
        account = 'Assets:Foo'
        balance = self.easy_parser.parse(text, easy_models.Balance)
        assert balance.raw_date.value == date
        assert balance.date == date
        assert balance.raw_account.value == account
        assert balance.account == account
        assert balance.raw_number.value == number
        assert balance.number == number
        if balance.raw_tolerance is None:
            assert tolerance is None
        else:
            assert balance.raw_tolerance.raw_number.value == tolerance
        assert balance.tolerance == tolerance
        assert balance.raw_currency.value == currency
        assert balance.currency == currency
        self.check_deepcopy_tree(balance)
        self.check_reattach_tree(balance)
        assert self.print_model(balance) == text

    @pytest.mark.parametrize(
        'text', [
            'balance Assets:Foo 100.00 USD',
            '2000-01-01 baLance Assets:Foo 100.00 USD',
            '2000-01-01 balance Assets:Foo',
            '2000-01-01 balance Assets:Foo 100.00',
            '2000-01-01 balance Assets:Foo USD',
            '2000-01-01 balance Assets:Foo 10+ USD',
            '2000-01-01 balance Assets:Foo 100.00 ~~ 0.01 USD',
            '2000-01-01 balance Assets:Foo 100.00 ~ 0.01 ~ 0.01 USD',
            '2000-01-01 balance Assets:Foo 100.00 USD ~ 0.01',
            '2000-01-01 balance Assets:Foo 100.00 USD ~ 0.01 USD',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse(text, raw_models.Balance)

    def test_set_raw_date(self) -> None:
        balance = self.raw_parser.parse('2000-01-01  balance Assets:Foo 100.00 USD', raw_models.Balance)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        balance.raw_date = new_date
        assert balance.raw_date is new_date
        assert self.print_model(balance) == '2012-12-12  balance Assets:Foo 100.00 USD'

    def test_set_date(self) -> None:
        balance = self.easy_parser.parse('2000-01-01  balance Assets:Foo 100.00 USD', easy_models.Balance)
        assert balance.date == datetime.date(2000, 1, 1)
        balance.date = datetime.date(2012, 12, 12)
        assert balance.date == datetime.date(2012, 12, 12)
        assert self.print_model(balance) == '2012-12-12  balance Assets:Foo 100.00 USD'

    def test_set_raw_account(self) -> None:
        balance = self.raw_parser.parse('2000-01-01  balance Assets:Foo  100.00 USD', raw_models.Balance)
        new_account = raw_models.Account.from_value('Assets:Bar')
        balance.raw_account = new_account
        assert balance.raw_account is new_account
        assert self.print_model(balance) == '2000-01-01  balance Assets:Bar  100.00 USD'

    def test_set_account(self) -> None:
        balance = self.easy_parser.parse('2000-01-01  balance Assets:Foo  100.00 USD', easy_models.Balance)
        assert balance.account == 'Assets:Foo'
        balance.account = 'Assets:Bar'
        assert balance.account == 'Assets:Bar'
        assert self.print_model(balance) == '2000-01-01  balance Assets:Bar  100.00 USD'

    def test_set_raw_number(self) -> None:
        balance = self.raw_parser.parse('2000-01-01 balance Assets:Foo  100.00  USD', raw_models.Balance)
        new_number = raw_models.NumberExpr.from_value(_D('-123.45'))
        balance.raw_number = new_number
        assert balance.raw_number is new_number
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo  -123.45  USD'

    def test_set_number(self) -> None:
        balance = self.easy_parser.parse('2000-01-01 balance Assets:Foo  100.00  USD', easy_models.Balance)
        assert balance.number == _D('100.00')
        balance.number = _D('-123.45')
        assert balance.number == _D('-123.45')
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo  -123.45  USD'

    @pytest.mark.parametrize(
        'text,raw_tolerance,expected', [
            ('2000-01-01 balance Assets:Foo 100.00  USD', None, '2000-01-01 balance Assets:Foo 100.00  USD'),
            ('2000-01-01 balance Assets:Foo 100.00  USD',
             raw_models.Tolerance.from_children(raw_models.NumberExpr.from_value(_D('0.01'))),
             '2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD'),
            ('2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD',
             raw_models.Tolerance.from_children(raw_models.NumberExpr.from_value(_D('0.02'))),
             '2000-01-01 balance Assets:Foo 100.00 ~ 0.02  USD'),
            ('2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD', None, '2000-01-01 balance Assets:Foo 100.00  USD'),
        ],
    )
    def test_set_raw_tolerance(self, text: str, raw_tolerance: Optional[raw_models.Tolerance], expected: str) -> None:
        balance = self.easy_parser.parse(text, easy_models.Balance)
        balance.raw_tolerance = raw_tolerance
        assert balance.raw_tolerance is raw_tolerance
        assert self.print_model(balance) == expected
        self.check_consistency(balance)

    @pytest.mark.parametrize(
        'text,tolerance,expected', [
            ('2000-01-01 balance Assets:Foo 100.00  USD', _D('0.01'), '2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD'),
            ('2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD', _D('0.02'), '2000-01-01 balance Assets:Foo 100.00 ~ 0.02  USD'),
            ('2000-01-01 balance Assets:Foo 100.00 ~ 0.01  USD', None, '2000-01-01 balance Assets:Foo 100.00  USD'),
        ],
    )
    def test_set_tolerance(self, text: str, tolerance: Optional[decimal.Decimal], expected: str) -> None:
        balance = self.easy_parser.parse(text, easy_models.Balance)
        balance.tolerance = tolerance
        assert balance.tolerance == tolerance
        assert self.print_model(balance) == expected
        self.check_consistency(balance)

    def test_set_raw_currency(self) -> None:
        balance = self.raw_parser.parse('2000-01-01 balance Assets:Foo 100.00  USD', raw_models.Balance)
        new_currency = raw_models.Currency.from_value('EUR')
        balance.raw_currency = new_currency
        assert balance.raw_currency is new_currency
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00  EUR'

    def test_set_currency(self) -> None:
        balance = self.easy_parser.parse('2000-01-01 balance Assets:Foo 100.00  USD', easy_models.Balance)
        assert balance.currency == 'USD'
        balance.currency = 'EUR'
        assert balance.currency == 'EUR'
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00  EUR'

    def test_from_children_with_tolerance(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2000, 1, 1))
        account = raw_models.Account.from_value('Assets:Foo')
        number = raw_models.NumberExpr.from_value(_D('100.00'))
        tolerance = raw_models.Tolerance.from_children(raw_models.NumberExpr.from_value(_D('0.01')))
        currency = raw_models.Currency.from_value('USD')
        balance = raw_models.Balance.from_children(date, account, number, tolerance, currency)
        assert balance.raw_date is date
        assert balance.raw_account is account
        assert balance.raw_number is number
        assert balance.raw_tolerance is tolerance
        assert balance.raw_currency is currency
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00 ~ 0.01 USD' 
        self.check_consistency(balance)

    def test_from_children_without_tolerance(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2000, 1, 1))
        account = raw_models.Account.from_value('Assets:Foo')
        number = raw_models.NumberExpr.from_value(_D('100.00'))
        currency = raw_models.Currency.from_value('USD')
        balance = raw_models.Balance.from_children(date, account, number, None, currency)
        assert balance.raw_date is date
        assert balance.raw_account is account
        assert balance.raw_number is number
        assert balance.raw_tolerance is None
        assert balance.raw_currency is currency
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00 USD' 
        self.check_consistency(balance)

    def test_from_value_with_tolerance(self) -> None:
        balance = easy_models.Balance.from_value(
            datetime.date(2000, 1, 1), 'Assets:Foo', _D('100.00'), _D('0.01'), 'USD')
        assert balance.raw_date.value == datetime.date(2000, 1, 1)
        assert balance.raw_account.value == 'Assets:Foo'
        assert balance.raw_number.value == _D('100.00')
        assert balance.raw_tolerance and balance.raw_tolerance.raw_number.value == _D('0.01')
        assert balance.raw_currency.value == 'USD'
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00 ~ 0.01 USD'
        self.check_consistency(balance)

    def test_from_value_without_tolerance(self) -> None:
        balance = easy_models.Balance.from_value(
            datetime.date(2000, 1, 1), 'Assets:Foo', _D('100.00'), None, 'USD')
        assert balance.raw_date.value == datetime.date(2000, 1, 1)
        assert balance.raw_account.value == 'Assets:Foo'
        assert balance.raw_number.value == _D('100.00')
        assert balance.raw_tolerance is None
        assert balance.raw_currency.value == 'USD'
        assert self.print_model(balance) == '2000-01-01 balance Assets:Foo 100.00 USD'
        self.check_consistency(balance)
