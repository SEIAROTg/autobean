import datetime
import itertools
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestOpen(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,account,currencies,booking', [
            ('2000-01-01 open Assets:Foo', datetime.date(2000, 1, 1), 'Assets:Foo', (), None),
            ('2000-01-01  open  Assets:Foo', datetime.date(2000, 1, 1), 'Assets:Foo', (), None),
            ('2000-01-01  open  Assets:Foo  USD', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD',), None),
            ('2000-01-01  open  Assets:Foo  USD, GBP, EUR', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD', 'GBP', 'EUR'), None),
            ('2000-01-01  open  Assets:Foo "NONE"', datetime.date(2000, 1, 1), 'Assets:Foo', (), 'NONE'),
            ('2000-01-01  open  Assets:Foo  USD, GBP, EUR "NONE"', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD', 'GBP', 'EUR'), 'NONE'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            account: str,
            currencies: tuple[str],
            booking: Optional[str],
    ) -> None:
        open = self.parser.parse(text, models.Open)
        assert open.first_token is open.raw_date
        assert open.raw_date.value == date
        assert open.date == date
        assert open.raw_account.value == account
        assert open.account == account
        assert open.raw_currencies == [
            models.Currency.from_value(currency) for currency in currencies
        ]
        assert tuple(open.currencies) == currencies
        if open.raw_booking is None:
            assert booking is None
        else:
            assert open.raw_booking.value == booking
        assert open.booking == booking
        assert self.print_model(open) == text
        self.check_deepcopy_tree(open)
        self.check_reattach_tree(open)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 Open Assets:Foo',
            '2000-01-01 open',
            '2000-01-01 open Assets:Foo USD GBP',
            '2000-01-01 open Assets:Foo USD NONE',
            'open Assets:Foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Open)

    def test_set_raw_date(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo', models.Open)
        open.raw_date.value = datetime.date(2012, 12, 12)
        assert open.date == datetime.date(2012, 12, 12)
        assert self.print_model(open) == '2012-12-12 open Assets:Foo'

    def test_set_date(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo', models.Open)
        open.date = datetime.date(2012, 12, 12)
        assert open.raw_date.value == datetime.date(2012, 12, 12)
        assert self.print_model(open) == '2012-12-12 open Assets:Foo'

    def test_set_raw_account(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo', models.Open)
        open.raw_account.value = 'Assets:Bar'
        assert open.account == 'Assets:Bar'
        assert self.print_model(open) == '2000-01-01 open Assets:Bar'

    def test_set_account(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo', models.Open)
        open.account = 'Assets:Bar'
        assert open.raw_account.value == 'Assets:Bar'
        assert self.print_model(open) == '2000-01-01 open Assets:Bar'

    def test_create_raw_currencies(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo', models.Open)
        currencies = [models.Currency.from_value('USD'), models.Currency.from_value('GBP')]
        open.raw_currencies.extend(currencies)
        assert open.currencies == ('USD', 'GBP')
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo USD, GBP'

    def test_create_currencies(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo', models.Open)
        open.currencies.extend(('USD', 'GBP'))
        assert open.currencies == ('USD', 'GBP')
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo USD, GBP'

    def test_insert_currencies(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo  USD,   GBP', models.Open)
        open.currencies.insert(1, 'EUR')
        assert open.currencies == ('USD', 'EUR', 'GBP')
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  USD, EUR,   GBP'
        open.currencies.insert(0, 'CHF')
        assert open.currencies == ('CHF', 'USD', 'EUR', 'GBP')
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  CHF, USD, EUR,   GBP'

    def test_remove_currencies(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo  USD,   EUR,    GBP', models.Open)
        open.currencies.remove('EUR')
        assert open.currencies == ['USD', 'GBP']
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  USD,    GBP'
        open.currencies.remove('USD')
        assert open.currencies == ['GBP']
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  GBP'
        open.currencies.remove('GBP')
        assert open.currencies == []
        assert self.print_model(open) == '2000-01-01 open Assets:Foo'

    def test_create_raw_booking(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo', models.Open)
        booking = models.EscapedString.from_value('NONE')
        open.raw_booking = booking
        assert open.raw_booking is booking
        assert open.booking == 'NONE'
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo "NONE"'

    def test_create_booking(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo', models.Open)
        open.booking = 'NONE'
        assert open.booking == 'NONE'
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo "NONE"'

    def test_update_raw_booking(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo  "NONE"', models.Open)
        booking = models.EscapedString.from_value('STRICT')
        open.raw_booking = booking
        assert open.raw_booking is booking
        assert open.booking == 'STRICT'
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  "STRICT"'

    def test_update_booking(self) -> None:
        open = self.parser.parse('2000-01-01 open Assets:Foo  "NONE"', models.Open)
        open.booking = 'STRICT'
        assert open.booking == 'STRICT'
        assert self.print_model(open) == '2000-01-01 open Assets:Foo  "STRICT"'

    def test_remove_raw_booking(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo  "NONE"', models.Open)
        open.raw_booking = None
        assert open.raw_booking is None
        assert open.booking is None
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo'

    def test_remove_booking(self) -> None:
        open = self.parser.parse('2000-01-01  open   Assets:Foo  "NONE"', models.Open)
        open.booking = None
        assert open.booking is None
        assert self.print_model(open) == '2000-01-01  open   Assets:Foo'

    @pytest.mark.parametrize(
        'text,date,account,currencies,booking', [
            ('2000-01-01 open Assets:Foo',
             models.Date.from_value(datetime.date(2000, 1, 1)),
             models.Account.from_value('Assets:Foo'),
             (),
             None),
            ('2000-01-01 open Assets:Foo USD',
             models.Date.from_value(datetime.date(2000, 1, 1)),
             models.Account.from_value('Assets:Foo'),
             (models.Currency.from_value('USD'),),
             None),
            ('2000-01-01 open Assets:Foo USD, GBP, EUR',
             models.Date.from_value(datetime.date(2000, 1, 1)),
             models.Account.from_value('Assets:Foo'),
             (models.Currency.from_value('USD'), models.Currency.from_value('GBP'), models.Currency.from_value('EUR')),
             None),
            ('2000-01-01 open Assets:Foo "NONE"',
             models.Date.from_value(datetime.date(2000, 1, 1)),
             models.Account.from_value('Assets:Foo'),
             (),
             models.EscapedString.from_value('NONE')),
            ('2000-01-01 open Assets:Foo USD, GBP, EUR "NONE"',
             models.Date.from_value(datetime.date(2000, 1, 1)),
             models.Account.from_value('Assets:Foo'),
             (models.Currency.from_value('USD'), models.Currency.from_value('GBP'), models.Currency.from_value('EUR')),
             models.EscapedString.from_value('NONE')),
        ],
    )
    def test_from_children(
            self,
            text: str,
            date: models.Date,
            account: models.Account,
            currencies: tuple[models.Currency, ...],
            booking: Optional[models.EscapedString],
    ) -> None:
        open = models.Open.from_children(date, account, currencies, booking)
        assert open.raw_date is date
        assert open.raw_account is account
        for actual, expected in itertools.zip_longest(open.raw_currencies, currencies):
            assert actual is expected
        assert open.raw_booking is booking
        assert self.print_model(open) == text

    @pytest.mark.parametrize(
        'text,date,account,currencies,booking', [
            ('2000-01-01 open Assets:Foo', datetime.date(2000, 1, 1), 'Assets:Foo', (), None),
            ('2000-01-01 open Assets:Foo USD', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD',), None),
            ('2000-01-01 open Assets:Foo USD, GBP, EUR', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD', 'GBP', 'EUR'), None),
            ('2000-01-01 open Assets:Foo "NONE"', datetime.date(2000, 1, 1), 'Assets:Foo', (), 'NONE'),
            ('2000-01-01 open Assets:Foo USD, GBP, EUR "NONE"', datetime.date(2000, 1, 1), 'Assets:Foo', ('USD', 'GBP', 'EUR'), 'NONE'),
        ],
    )
    def test_from_value(
            self,
            text: str,
            date: datetime.date,
            account: str,
            currencies: tuple[str],
            booking: Optional[str],
    ) -> None:
        open = models.Open.from_value(date, account, currencies, booking)
        assert open.date == date
        assert open.account == account
        assert open.currencies == list(currencies)
        assert open.booking == booking
        assert self.print_model(open) == text
