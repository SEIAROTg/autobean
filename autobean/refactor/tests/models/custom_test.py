import datetime
import decimal
import itertools
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base

_D = decimal.Decimal


class TestCustom(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,type,values', [
            ('2000-01-01 custom "foo"', datetime.date(2000, 1, 1), 'foo', ()),
            ('2000-01-01  custom  "foo"  "bar"', datetime.date(2000, 1, 1), 'foo', ('bar',)),
            ('2000-01-01  custom  "foo"  "bar" 2020-12-30 100.00 TRUE 123.45 USD Assets:Foo', datetime.date(2000, 1, 1), 'foo',
             ('bar', datetime.date(2020, 12, 30), _D(100.00), True, models.Amount.from_value(_D('123.45'), 'USD'), models.Account.from_value('Assets:Foo'))),
            ('2000-01-01  custom  "foo"  10  -2', datetime.date(2000, 1, 1), 'foo', (_D(8),)),
            ('2000-01-01  custom  "foo"  10  (-2)', datetime.date(2000, 1, 1), 'foo', (_D(10), _D(-2))),
            ('2000-01-01  custom  "foo"  10  -2 USD', datetime.date(2000, 1, 1), 'foo', (models.Amount.from_value(_D(8), 'USD'),)),
            ('2000-01-01  custom  "foo"  10  (-2) USD', datetime.date(2000, 1, 1), 'foo', (_D(10), models.Amount.from_value(_D(-2), 'USD'),)),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            type: str,
            values: tuple[models.CustomValue, ...],
    ) -> None:
        custom = self.parser.parse(text, models.Custom)
        assert custom.raw_date.value == date
        assert custom.date == date
        assert custom.raw_type.value == type
        assert custom.type == type
        for actual, expected in itertools.zip_longest(custom.raw_values, values):
            if isinstance(actual, models.Amount):
                assert isinstance(expected, models.Amount)
                assert actual.number == expected.number
                assert actual.currency == expected.currency
            elif isinstance(actual, models.Account):
                assert actual == expected
            else:
                assert actual.value == expected
        for actual, expected in itertools.zip_longest(custom.values, values):
            if isinstance(actual, models.Amount):
                assert isinstance(expected, models.Amount)
                assert actual.number == expected.number
                assert actual.currency == expected.currency
            else:
                assert actual == expected
        assert custom.raw_values is custom.raw_values
        assert self.print_model(custom) == text
        self.check_deepcopy_tree(custom)
        self.check_reattach_tree(custom)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 Custom "foo"',
            '2000-01-01 custom',
            '2000-01-01 custom "foo" #bar',
            '2000-01-01 custom "foo" ^bar',
            '2000-01-01 custom "foo" USD',
            '2000-01-01 custom "foo" NULL',
            '2000-01-01 custom "foo" 1, 2',
            'custom "foo"',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Custom)

    def test_set_raw_date(self) -> None:
        custom = self.parser.parse('2000-01-01 custom "foo"', models.Custom)
        new_date = models.Date.from_value(datetime.date(2012, 12, 12))
        custom.raw_date = new_date
        assert custom.raw_date is new_date
        assert custom.date == datetime.date(2012, 12, 12)
        assert self.print_model(custom) == '2012-12-12 custom "foo"'

    def test_set_date(self) -> None:
        custom = self.parser.parse('2000-01-01 custom "foo"', models.Custom)
        custom.date = datetime.date(2012, 12, 12)
        assert custom.raw_date.value == datetime.date(2012, 12, 12)
        assert custom.date == datetime.date(2012, 12, 12)
        assert self.print_model(custom) == '2012-12-12 custom "foo"'

    def test_set_raw_type(self) -> None:
        custom = self.parser.parse('2000-01-01 custom "foo"', models.Custom)
        new_type = models.EscapedString.from_value('bar')
        custom.raw_type = new_type
        assert custom.raw_type is new_type
        assert custom.type == 'bar'
        assert self.print_model(custom) == '2000-01-01 custom "bar"'

    def test_set_type(self) -> None:
        custom = self.parser.parse('2000-01-01 custom "foo"', models.Custom)
        custom.type = 'bar'
        assert custom.raw_type.value == 'bar'
        assert custom.type == 'bar'
        assert self.print_model(custom) == '2000-01-01 custom "bar"'

    def test_extend_raw_values(self) -> None:
        custom = self.parser.parse('2000-01-01  custom   "foo"', models.Custom)
        new_values: list[models.CustomRawValue] = [
            models.EscapedString.from_value('bar'),
            models.Date.from_value(datetime.date(2012, 12, 12)),
            models.Bool.from_value(False),
            models.NumberExpr.from_value(_D(10)),
            models.Amount.from_value(_D(20), 'USD'),
            models.Account.from_value('Assets:Foo'),
        ]
        custom.raw_values.extend(new_values)
        for actual, expected in itertools.zip_longest(custom.raw_values, new_values):
            assert actual is expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo')

    def test_extend_values(self) -> None:
        custom = self.parser.parse('2000-01-01  custom   "foo"', models.Custom)
        new_values: list[models.CustomValue] = [
            'bar',
            datetime.date(2012, 12, 12),
            False,
            _D(10),
            models.Amount.from_value(_D(20), 'USD'),
            models.Account.from_value('Assets:Foo'),
        ]
        custom.values.extend(new_values)
        for actual, expected in itertools.zip_longest(custom.values, new_values):
            assert actual == expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo')

    def test_update_raw_values(self) -> None:
        custom = self.parser.parse(
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo', models.Custom)
        new_values: list[models.CustomRawValue] = [
            models.EscapedString.from_value('baz'),
            models.Date.from_value(datetime.date(2000, 1, 1)),
            models.Bool.from_value(True),
            models.NumberExpr.from_value(_D(12)),
            models.Amount.from_value(_D(34), 'EUR'),
            models.Account.from_value('Assets:Bar'),
        ]
        custom.raw_values[:] = new_values
        for actual, expected in itertools.zip_longest(custom.raw_values, new_values):
            assert actual is expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" "baz" 2000-01-01 TRUE 12 34 EUR Assets:Bar')

    def test_update_values(self) -> None:
        custom = self.parser.parse(
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo', models.Custom)
        original_raw_values = custom.raw_values[:]
        new_values: list[models.CustomValue] = [
            'baz',
            datetime.date(2000, 1, 1),
            True,
            _D(12),
            models.Amount.from_value(_D(34), 'EUR'),
            models.Account.from_value('Assets:Bar'),
        ]
        custom.values[:] = new_values
        for actual, original, expected in itertools.zip_longest(
                custom.raw_values, original_raw_values, new_values):
            if isinstance(actual, models.Amount | models.Account):
                assert actual is expected
            else:
                assert actual is original
                assert actual.value == expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" "baz" 2000-01-01 TRUE 12 34 EUR Assets:Bar')

    def test_replace_raw_values(self) -> None:
        custom = self.parser.parse(
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo', models.Custom)
        new_values: list[models.CustomRawValue] = [
            models.Date.from_value(datetime.date(2000, 1, 1)),
            models.Bool.from_value(True),
            models.NumberExpr.from_value(_D(12)),
            models.Amount.from_value(_D(34), 'EUR'),
            models.Account.from_value('Assets:Bar'),
            models.EscapedString.from_value('baz'),
        ]
        custom.raw_values[:] = new_values
        for actual, expected in itertools.zip_longest(custom.raw_values, new_values):
            assert actual is expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" 2000-01-01 TRUE 12 34 EUR Assets:Bar "baz"')

    def test_replace_values(self) -> None:
        custom = self.parser.parse(
            '2000-01-01  custom   "foo" "bar" 2012-12-12 FALSE 10 20 USD Assets:Foo', models.Custom)
        original_raw_values = custom.raw_values[:]
        new_values: list[models.CustomValue] = [
            datetime.date(2000, 1, 1),
            True,
            _D(12),
            models.Amount.from_value(_D(34), 'EUR'),
            models.Account.from_value('Assets:Bar'),
            'baz',
        ]
        custom.values[:] = new_values
        for actual, original, expected in itertools.zip_longest(
                custom.raw_values, original_raw_values, new_values):
            if isinstance(actual, models.Amount | models.Account):
                assert actual is expected
            else:
                assert actual.value == expected
        assert self.print_model(custom) == (
            '2000-01-01  custom   "foo" 2000-01-01 TRUE 12 34 EUR Assets:Bar "baz"')

    def test_from_children_empty_values(self) -> None:
        custom = models.Custom.from_children(
            models.Date.from_value(datetime.date(2000, 1, 1)),
            models.EscapedString.from_value('foo'),
            (),
        )
        assert custom.raw_date.value == datetime.date(2000, 1, 1)
        assert custom.date == datetime.date(2000, 1, 1)
        assert custom.raw_type.value == 'foo'
        assert custom.type == 'foo'
        assert custom.raw_values == []
        assert custom.values == []
        assert self.print_model(custom) == '2000-01-01 custom "foo"'

    def test_from_value_empty_values(self) -> None:
        custom = models.Custom.from_value(
            datetime.date(2000, 1, 1),
            'foo',
            (),
        )
        assert custom.date == datetime.date(2000, 1, 1)
        assert custom.type == 'foo'
        assert custom.values == []
        assert self.print_model(custom) == '2000-01-01 custom "foo"'

    def test_from_children_some_values(self) -> None:
        values: list[models.CustomRawValue] = [
            models.EscapedString.from_value('bar'),
            models.Date.from_value(datetime.date(2012, 12, 12)),
            models.Bool.from_value(False),
            models.NumberExpr.from_value(_D(10)),
            models.Amount.from_children(
                +models.NumberExpr.from_value(_D('2.00')) * _D('3'),
                models.Currency.from_value('USD')),
            models.NumberExpr.from_value(_D(10)),
            models.NumberExpr.from_value(_D(-2)),
            models.Account.from_value('Assets:Foo'),
        ]
        custom = models.Custom.from_children(
            models.Date.from_value(datetime.date(2000, 1, 1)),
            models.EscapedString.from_value('foo'),
            values,
        )
        for actual, expected in itertools.zip_longest(custom.raw_values, values):
            assert actual is expected
        assert self.print_model(custom) == (
            '2000-01-01 custom "foo" "bar" 2012-12-12 FALSE 10 (+2.00 * 3) USD 10 (-2) Assets:Foo')

    def test_from_value_some_values(self) -> None:
        values: list[models.CustomValue | models.CustomRawValue] = [
            'bar',
            datetime.date(2012, 12, 12),
            False,
            _D(10),
            models.Amount.from_children(
                +models.NumberExpr.from_value(_D('2.00')) * _D('3'),
                models.Currency.from_value('USD')),
            models.NumberExpr.from_value(_D(10)),
            _D(-2),
            models.Account.from_value('Assets:Foo'),
        ]
        custom = models.Custom.from_value(datetime.date(2000, 1, 1), 'foo', values)
        for actual, expected in itertools.zip_longest(custom.values, values):
            if isinstance(expected, models.NumberExpr):
                assert actual == expected.value
            else:
                assert actual == expected
        assert self.print_model(custom) == (
            '2000-01-01 custom "foo" "bar" 2012-12-12 FALSE 10 (+2.00 * 3) USD 10 (-2) Assets:Foo')
