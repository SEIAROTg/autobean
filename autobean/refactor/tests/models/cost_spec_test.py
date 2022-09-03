import datetime
import decimal
from typing import Optional, Type
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base

_D = decimal.Decimal

_NUMBER_PER_TESTCASES = [
    # CompoundAmount
    ('{*, "foo", 12.34 # 56.78 USD}', _D('90.12'), '{*, "foo", 90.12 # 56.78 USD}'),
    ('{12.34 # 56.78 USD}', _D('90.12'), '{90.12 # 56.78 USD}'),
    ('{12.34 # 56.78 USD}', None, '{# 56.78 USD}'),
    ('{# 56.78 USD}', _D('90.12'), '{90.12 # 56.78 USD}'),
    ('{12.34 # USD}', _D('90.12'), '{90.12 # USD}'),
    # Amount(per)
    ('{12.34 USD}', _D('56.78'), '{56.78 USD}'),
    # Amount(per) - Number(per) -> Currency(per)
    ('{12.34 USD}', None, '{USD}'),
    # Currency(per) + Number(per) -> Amount(per)
    ('{USD}', _D('56.78'), '{56.78 USD}'),
    # Number(per)
    ('{}', None, '{}'),
    ('{}', _D('12.34'), '{12.34}'),
    ('{12.34}', _D('56.78'), '{56.78}'),
    ('{12.34}', None, '{}'),
    # Amount(total) + Number(per) -> CompoundAmount
    ('{{12.34 USD}}', _D('56.78'), '{56.78 # 12.34 USD}'),
    # Currency(total) + Number(per) -> Amount(per)
    ('{{USD}}', _D('56.78'), '{56.78 USD}'),
    # /(total) -> Number(per) -> Number(per)
    ('{{}}', _D('12.34'), '{12.34}'),
    ('{{2000-01-01}}', _D('12.34'), '{12.34, 2000-01-01}'),
]

_NUMBER_TOTAL_TESTCASES = [
    # CompoundAmount
    ('{*, "foo", 12.34 # 56.78 USD}', _D('90.12'), '{*, "foo", 12.34 # 90.12 USD}'),
    ('{12.34 # 56.78 USD}', _D('90.12'), '{12.34 # 90.12 USD}'),
    ('{12.34 # 56.78 USD}', None, '{12.34 # USD}'),
    ('{# 56.78 USD}', _D('90.12'), '{# 90.12 USD}'),
    ('{12.34 # USD}', _D('90.12'), '{12.34 # 90.12 USD}'),
    # Amount(total)
    ('{{12.34 USD}}', _D('56.78'), '{{56.78 USD}}'),
    # Amount(total) - Number(total) -> Currency(total)
    ('{{12.34 USD}}', None, '{{USD}}'),
    # Currency(total) + Number(total) -> Amount(total)
    ('{{USD}}', _D('56.78'), '{{56.78 USD}}'),
    # Number(total)
    ('{{}}', None, '{{}}'),
    ('{{}}', _D('12.34'), '{{12.34}}'),
    ('{{12.34}}', _D('56.78'), '{{56.78}}'),
    ('{{12.34}}', None, '{{}}'),
    # Amount(per) + Number(total) -> CompoundAmount
    ('{12.34 USD}', _D('56.78'), '{12.34 # 56.78 USD}'),
    # Currency(per) + Number(total) -> Amount(total)
    ('{USD}', _D('56.78'), '{{56.78 USD}}'),
    # /(per) -> Number(total) -> Number(total)
    ('{}', _D('12.34'), '{{12.34}}'),
    ('{2000-01-01}', _D('12.34'), '{{12.34, 2000-01-01}}'),
]

_CURRENCY_TESTCASES = [
    # CompoundAmount
    ('{12.34 # 56.78 USD}', 'EUR', '{12.34 # 56.78 EUR}'),
    # CompoundAmount - Currency
    ('{12.34 # USD}', None, '{12.34}'),
    ('{# 56.78 USD}', None, '{{56.78}}'),
    ('{# USD}', None, '{}'),
    ('{# USD, 2000-01-01}', None, '{2000-01-01}'),
    # Amount
    ('{12.34 USD}', 'EUR', '{12.34 EUR}'),
    ('{{12.34 USD}}', 'EUR', '{{12.34 EUR}}'),
    # Amount - Currency -> Number
    ('{12.34 USD}', None, '{12.34}'),
    ('{{12.34 USD}}', None, '{{12.34}}'),
    # Currency
    ('{USD}', 'EUR', '{EUR}'),
    ('{USD}', None, '{}'),
    ('{USD, 2000-01-01}', None, '{2000-01-01}'),
]

_MERGE_TEST_CASES = [
    ('{12.34 USD}', True, '{12.34 USD, *}'),
    ('{12.34 USD, 2000-01-01}', True, '{12.34 USD, 2000-01-01, *}'),
    ('{{12.34 USD}}', False, '{{12.34 USD}}'),
    ('{12.34 USD, *, 2000-01-01}', False, '{12.34 USD, 2000-01-01}'),
    ('{12.34 USD, *, 2000-01-01}', True, '{12.34 USD, *, 2000-01-01}'),
]


class TestCostSpec(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,cost_type,number_per,number_total,currency,date,label,merge', [
            ('{}', models.UnitCost, None, None, None, None, None, False),
            ('{{}}', models.TotalCost, None, None, None, None, None, False),
            ('{12.34}', models.UnitCost, _D('12.34'), None, None, None, None, False),
            ('{{12.34}}', models.TotalCost, None, _D('12.34'), None, None, None, False),
            ('{USD}', models.UnitCost, None, None, 'USD', None, None, False),
            ('{{USD}}', models.TotalCost, None, None, 'USD', None, None, False),
            ('{12.34 USD}', models.UnitCost, _D('12.34'), None, 'USD', None, None, False),
            ('{{12.34 USD}}', models.TotalCost, None, _D('12.34'), 'USD', None, None, False),
            ('{12.34 # 56.78 USD}', models.UnitCost, _D('12.34'), _D('56.78'), 'USD', None, None, False),
            ('{# 56.78 USD}', models.UnitCost, None, _D('56.78'), 'USD', None, None, False),
            ('{12.34 # USD}', models.UnitCost, _D('12.34'), None, 'USD', None, None, False),
            ('{12.34 USD, 2000-01-01, *}', models.UnitCost, _D('12.34'), None, 'USD', datetime.date(2000,1,1), None, True),
            ('{12.34 USD, 2000-01-01, "foo"}', models.UnitCost, _D('12.34'), None, 'USD', datetime.date(2000,1,1), 'foo', False),
            ('{"foo", 12.34 USD, 2000-01-01}', models.UnitCost, _D('12.34'), None, 'USD', datetime.date(2000,1,1), 'foo', False),
            # below are not really valid but we don't reject them in the parsing phase
            ('{{12.34 # 56.78 USD}}', models.TotalCost, _D('12.34'), _D('56.78'), 'USD', None, None, False),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            cost_type: Type[models.UnitCost | models.TotalCost],
            number_per: Optional[decimal.Decimal],
            number_total: Optional[decimal.Decimal],
            currency: Optional[str],
            date: Optional[datetime.date],
            label: Optional[str],
            merge: bool,
    ) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        assert isinstance(cost_spec.raw_cost, cost_type)
        assert cost_spec.number_per == number_per
        assert cost_spec.number_total == number_total
        assert cost_spec.currency == currency
        assert cost_spec.date == date
        assert cost_spec.label == label
        assert cost_spec.merge == merge
        assert self.print_model(cost_spec) == text
        self.check_deepcopy_tree(cost_spec)
        self.check_reattach_tree(cost_spec)

    @pytest.mark.parametrize(
        'text', [
            '{{{}}}',
            '{{}',
            '{}}',
            '{#foo}',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_inline(text, models.CostSpec)

    @pytest.mark.parametrize('text,value,expected', _NUMBER_PER_TESTCASES)
    def test_set_raw_number_per(self, text: str, value: Optional[decimal.Decimal], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        number_per = models.NumberExpr.from_value(value) if value is not None else None
        cost_spec.raw_number_per = number_per
        assert cost_spec.raw_number_per is number_per
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _NUMBER_PER_TESTCASES)
    def test_set_number_per(self, text: str, value: Optional[decimal.Decimal], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        cost_spec.number_per = value
        assert cost_spec.number_per == value
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _NUMBER_TOTAL_TESTCASES)
    def test_set_raw_number_total(self, text: str, value: Optional[decimal.Decimal], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        number_total = models.NumberExpr.from_value(value) if value is not None else None
        cost_spec.raw_number_total = number_total
        assert cost_spec.raw_number_total is number_total
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _NUMBER_TOTAL_TESTCASES)
    def test_set_number_total(self, text: str, value: Optional[decimal.Decimal], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        cost_spec.number_total = value
        assert cost_spec.number_total == value
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _CURRENCY_TESTCASES)
    def test_set_raw_currency(self, text: str, value: Optional[str], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        currency = models.Currency.from_value(value) if value is not None else None
        cost_spec.raw_currency = currency
        assert cost_spec.raw_currency is currency
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _CURRENCY_TESTCASES)
    def test_set_currency(self, text: str, value: Optional[str], expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        cost_spec.currency = value
        assert cost_spec.currency == value
        assert self.print_model(cost_spec) == expected

    @pytest.mark.parametrize('text,value,expected', _MERGE_TEST_CASES)
    def test_set_merge(self, text: str, value: bool, expected: str) -> None:
        cost_spec = self.parser.parse_inline(text, models.CostSpec)
        cost_spec.merge = value
        assert cost_spec.merge == value
        assert self.print_model(cost_spec) == expected

    def test_from_children(self) -> None:
        number = models.NumberExpr.from_value(_D('12.34'))
        currency = models.Currency.from_value('USD')
        amount = models.Amount.from_children(number, currency)
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        label = models.EscapedString.from_value('foo')
        asterisk = models.Asterisk.from_default()
        total_cost = models.TotalCost.from_children([amount, date, label, asterisk])
        cost_spec = models.CostSpec.from_children(total_cost)
        assert cost_spec.raw_compound_amount_comp is None
        assert cost_spec.raw_amount_comp is amount
        assert cost_spec.raw_number_comp is None
        assert cost_spec.raw_currency_comp is None
        assert cost_spec.raw_date_comp is date
        assert cost_spec.raw_label_comp is label
        assert cost_spec.raw_asterisk_comp is asterisk
        assert cost_spec.raw_number_per is None
        assert cost_spec.number_per is None
        assert cost_spec.raw_number_total is number
        assert cost_spec.number_total == _D('12.34')
        assert cost_spec.raw_date is date
        assert cost_spec.date == datetime.date(2000, 1, 1)
        assert cost_spec.raw_label is label
        assert cost_spec.label == 'foo'
        assert cost_spec.merge == True
        assert self.print_model(cost_spec) == '{{12.34 USD, 2000-01-01, "foo", *}}'

    @pytest.mark.parametrize(
        'text,cost_type,number_per,number_total,currency,date,label,merge', [
            ('{}', models.UnitCost, None, None, None, None, None, False),
            ('{12.34}', models.UnitCost, _D('12.34'), None, None, None, None, False),
            ('{{12.34}}', models.TotalCost, None, _D('12.34'), None, None, None, False),
            ('{USD}', models.UnitCost, None, None, 'USD', None, None, False),
            ('{12.34 USD}', models.UnitCost, _D('12.34'), None, 'USD', None, None, False),
            ('{{12.34 USD}}', models.TotalCost, None, _D('12.34'), 'USD', None, None, False),
            ('{12.34 # 56.78 USD}', models.UnitCost, _D('12.34'), _D('56.78'), 'USD', None, None, False),
            ('{12.34 USD, 2000-01-01, *}', models.UnitCost, _D('12.34'), None, 'USD', datetime.date(2000,1,1), None, True),
            ('{12.34 USD, 2000-01-01, "foo"}', models.UnitCost, _D('12.34'), None, 'USD', datetime.date(2000,1,1), 'foo', False),
        ],
    )
    def test_from_value(
            self,
            text: str,
            cost_type: Type[models.UnitCost | models.TotalCost],
            number_per: Optional[decimal.Decimal],
            number_total: Optional[decimal.Decimal],
            currency: Optional[str],
            date: Optional[datetime.date],
            label: Optional[str],
            merge: bool,
    ) -> None:
        cost_spec = models.CostSpec.from_value(number_per, number_total, currency, date, label, merge)
        assert isinstance(cost_spec.raw_cost, cost_type)
        assert cost_spec.number_per == number_per
        assert cost_spec.number_total == number_total
        assert cost_spec.currency == currency
        assert cost_spec.date == date
        assert cost_spec.label == label
        assert cost_spec.merge == merge
        assert self.print_model(cost_spec) == text
