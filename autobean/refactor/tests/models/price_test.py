import datetime
import decimal
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestPrice(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,currency,number,ref_currency', [
            ('2000-01-01 price GBP 1.5 USD', datetime.date(2000, 1, 1), 'GBP', decimal.Decimal('1.5'), 'USD'),
            ('2000-01-01  price  GBP  1 + 0.5  USD', datetime.date(2000, 1, 1), 'GBP', decimal.Decimal('1.5'), 'USD'),
        ],
    )
    def test_parse_success(self, text: str, date: datetime.date, currency: str, number: decimal.Decimal, ref_currency: str) -> None:
        price = self.easy_parser.parse(text, easy_models.Price)
        assert price.raw_date.value == date
        assert price.date == date
        assert price.raw_currency.value == currency
        assert price.currency == currency
        assert price.raw_amount.raw_number.value == number
        assert price.amount.raw_number.value == number
        assert price.raw_amount.raw_currency.value == ref_currency
        assert price.amount.raw_currency.value == ref_currency
        self.check_deepcopy_tree(price)
        self.check_reattach_tree(price)

    @pytest.mark.parametrize(
        'text', [
            'price GBP 1.5 USD',
            '2000-01-01 price GBP',
            '2000-01-01 price GBP 1.5',
            '2000-01-01 price GBP USD',
            '2000-01-01 price 1.5 USD',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse(text, raw_models.Price)

    def test_set_raw_date(self) -> None:
        price = self.raw_parser.parse('2000-01-01 price GBP 1.5 USD', raw_models.Price)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        price.raw_date = new_date
        assert price.raw_date is new_date
        assert self.print_model(price) == '2012-12-12 price GBP 1.5 USD'

    def test_set_date(self) -> None:
        price = self.easy_parser.parse('2000-01-01  price GBP 1.5 USD', easy_models.Price)
        assert price.date == datetime.date(2000, 1, 1)
        price.date = datetime.date(2012, 12, 12)
        assert price.date == datetime.date(2012, 12, 12)
        assert self.print_model(price) == '2012-12-12  price GBP 1.5 USD'

    def test_set_raw_currency(self) -> None:
        price = self.raw_parser.parse('2000-01-01 price  GBP  1.5 USD', raw_models.Price)
        new_currency = raw_models.Currency.from_value('EUR')
        price.raw_currency = new_currency
        assert price.raw_currency is new_currency
        assert self.print_model(price) == '2000-01-01 price  EUR  1.5 USD'

    def test_set_currency(self) -> None:
        price = self.easy_parser.parse('2000-01-01 price  GBP  1.5 USD', easy_models.Price)
        assert price.currency == 'GBP'
        price.currency = 'EUR'
        assert price.currency == 'EUR'
        assert self.print_model(price) == '2000-01-01 price  EUR  1.5 USD'

    def test_set_raw_amount(self) -> None:
        price = self.raw_parser.parse('2000-01-01 price GBP  1.5 USD', raw_models.Price)
        new_amount = easy_models.Amount.from_value(decimal.Decimal('1.3'), 'EUR')
        price.raw_amount = new_amount
        assert price.raw_amount is new_amount
        assert self.print_model(price) == '2000-01-01 price GBP  1.3 EUR'

    def test_set_amount(self) -> None:
        price = self.easy_parser.parse('2000-01-01 price GBP  1.5 USD', easy_models.Price)
        new_amount = easy_models.Amount.from_value(decimal.Decimal('1.3'), 'EUR')
        price.amount = new_amount
        assert price.raw_amount is new_amount
        assert self.print_model(price) == '2000-01-01 price GBP  1.3 EUR'

    def test_from_children(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2000, 1, 1))
        currency = raw_models.Currency.from_value('GBP')
        number = raw_models.NumberExpr.from_value(decimal.Decimal('1.5'))
        ref_currency = raw_models.Currency.from_value('USD')
        amount = raw_models.Amount.from_children(number, ref_currency)
        price = raw_models.Price.from_children(date, currency, amount)
        assert price.raw_date is date
        assert price.raw_currency is currency
        assert price.raw_amount is amount
        assert price.raw_amount.raw_number is number
        assert price.raw_amount.raw_currency is ref_currency
        assert self.print_model(price) == '2000-01-01 price GBP 1.5 USD'
        self.check_consistency(price)

    def test_from_value(self) -> None:
        price = easy_models.Price.from_value(
            datetime.date(2000, 1, 1),
            'GBP',
            easy_models.Amount.from_value(decimal.Decimal('1.5'), 'USD'))
        assert price.raw_date.value == datetime.date(2000, 1, 1)
        assert price.raw_currency.value == 'GBP'
        assert price.raw_amount.raw_number.value == decimal.Decimal('1.5')
        assert price.raw_amount.raw_currency.value == 'USD'
        assert self.print_model(price) == '2000-01-01 price GBP 1.5 USD'
        self.check_consistency(price)
        self.check_flavor_consistency(price)
