import decimal
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base

_D = decimal.Decimal

_FLAG_TESTCASES = [
    ('    Assets:Foo 100.00 USD', '*', '    * Assets:Foo 100.00 USD'),
    ('    Assets:Foo 100.00 USD', None, '    Assets:Foo 100.00 USD'),
    ('    *  Assets:Foo 100.00 USD', '!', '    !  Assets:Foo 100.00 USD'),
    ('    *  Assets:Foo 100.00 USD', None, '    Assets:Foo 100.00 USD'),
]
_NUMBER_TESTCASES = [
    ('    Assets:Foo  USD', _D('100.00'), '    Assets:Foo 100.00  USD'),
    ('    Assets:Foo  100.00   USD', None, '    Assets:Foo   USD'),
    ('    Assets:Foo  100.00   USD', _D('100.00'), '    Assets:Foo  100.00   USD'),
    ('    Assets:Foo  100.00', None, '    Assets:Foo'),
    ('    Assets:Foo  100.00   USD', _D('123.45'), '    Assets:Foo  123.45   USD'),
]
_CURRENCY_TESTCASES = [
    ('    Assets:Foo  100.00', 'USD', '    Assets:Foo  100.00 USD'),
    ('    Assets:Foo  100.00   USD', None, '    Assets:Foo  100.00'),
    ('    Assets:Foo  100.00   USD', 'USD', '    Assets:Foo  100.00   USD'),
    ('    Assets:Foo  USD', None, '    Assets:Foo'),
    ('    Assets:Foo  100.00   USD', 'GBP', '    Assets:Foo  100.00   GBP'),
]
def _constructor_testcases() -> list:
    return [
        ('    Assets:Foo 100.00 USD', None, 'Assets:Foo', _D('100.00'), 'USD', None, None),
        ('    * Assets:Foo 100.00 USD', '*', 'Assets:Foo', _D('100.00'), 'USD', None, None),
        ('    Assets:Foo 100.00', None, 'Assets:Foo', _D('100.00'), None, None, None),
        ('    Assets:Foo USD', None, 'Assets:Foo', None, 'USD', None, None),
        ('    Assets:Foo', None, 'Assets:Foo', None, None, None, None),
        ('    Assets:Foo 100.00 USD @@ 80 GBP', None, 'Assets:Foo', _D('100.00'), 'USD', None, models.TotalPrice.from_value(_D(80), 'GBP')),
        ('    Assets:Foo 100.00 USD @', None, 'Assets:Foo', _D('100.00'), 'USD', None, models.UnitPrice.from_value(None, None)),
        ('    Assets:Foo @', None, 'Assets:Foo', None, None, None, models.UnitPrice.from_value(None, None)),
        ('    Assets:Foo 100.00 USD {1.25 GBP}', None, 'Assets:Foo', _D('100.00'), 'USD', models.CostSpec.from_value(_D('1.25'), None, 'GBP'), None),
        ('    Assets:Foo {}', None, 'Assets:Foo', None, None, models.CostSpec.from_value(None, None, None), None),
        ('    Assets:Foo 100.00 USD {1.25 GBP} @@ 80 GBP', None, 'Assets:Foo', _D('100.00'), 'USD', models.CostSpec.from_value(_D('1.25'), None, 'GBP'), models.TotalPrice.from_value(_D(80), 'GBP')),
    ]

class TestPosting(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,flag,account,number,currency,cost,price', _constructor_testcases(),
    )
    def test_parse_success(
            self,
            text: str,
            flag: Optional[models.PostingFlag],
            account: str,
            number: Optional[decimal.Decimal],
            currency: Optional[str],
            cost: Optional[models.CostSpec],
            price: Optional[models.PriceAnnotation],
    ) -> None:
        posting = self.parser.parse(text, models.Posting)
        assert posting.indent == '    '
        assert posting.flag == flag
        assert posting.account == account
        assert posting.number == number
        assert posting.currency == currency
        assert posting.raw_cost == cost
        assert posting.raw_price == price
        assert self.print_model(posting) == text
        self.check_deepcopy_tree(posting)
        self.check_reattach_tree(posting)

    @pytest.mark.parametrize(
        'text', [
            'Assets:Foo 100.00 USD',
            '    100.00 USD',
            '    Assets:Foo 100.00 USD @ 1.25 GBP @@ 80 GBP',
            '    Assets:Foo 100.00 USD @@ 80 GBP {1.25 GBP}',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Posting)

    @pytest.mark.parametrize(
        'text,flag,expected_text', _FLAG_TESTCASES,
    )
    def test_set_raw_flag(self, text: str, flag: Optional[str], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        raw_flag = models.PostingFlag.from_value(flag) if flag is not None else None
        posting.raw_flag = raw_flag
        assert posting.raw_flag is raw_flag
        assert posting.flag == flag
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,flag,expected_text', _FLAG_TESTCASES,
    )
    def test_set_flag(self, text: str, flag: Optional[str], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        posting.flag = flag
        assert posting.flag == flag
        assert self.print_model(posting) == expected_text

    def test_set_raw_account(self) -> None:
        posting = self.parser.parse('    Assets:Foo 100.00 USD', models.Posting)
        new_account = models.Account.from_value('Assets:Bar')
        posting.raw_account = new_account
        assert posting.raw_account is new_account
        assert posting.account == 'Assets:Bar'
        assert self.print_model(posting) == '    Assets:Bar 100.00 USD'

    def test_set_account(self) -> None:
        posting = self.parser.parse('    Assets:Foo 100.00 USD', models.Posting)
        posting.account = 'Assets:Bar'
        assert posting.account == 'Assets:Bar'
        assert self.print_model(posting) == '    Assets:Bar 100.00 USD'

    @pytest.mark.parametrize(
        'text,number,expected_text', _NUMBER_TESTCASES,
    )
    def test_set_raw_number(self, text: str, number: Optional[decimal.Decimal], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        raw_number = models.NumberExpr.from_value(number) if number is not None else None
        posting.raw_number = raw_number
        assert posting.raw_number is raw_number
        assert posting.number == number
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,number,expected_text', _NUMBER_TESTCASES,
    )
    def test_set_number(self, text: str, number: Optional[decimal.Decimal], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        posting.number = number
        assert posting.number == number
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,currency,expected_text', _CURRENCY_TESTCASES,
    )
    def test_set_raw_currency(self, text: str, currency: Optional[str], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        raw_currency = models.Currency.from_value(currency) if currency is not None else None
        posting.raw_currency = raw_currency
        assert posting.raw_currency is raw_currency
        assert posting.currency == currency
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,currency,expected_text', _CURRENCY_TESTCASES,
    )
    def test_set_currency(self, text: str, currency: Optional[str], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        posting.currency = currency
        assert posting.currency == currency
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,cost,expected_text', [
            ('    Assets:Foo 100.00 USD', None, '    Assets:Foo 100.00 USD'),
            ('    Assets:Foo 100.00 USD', models.CostSpec.from_value(_D('12.34'), _D('56.78'), 'GBP'), '    Assets:Foo 100.00 USD {12.34 # 56.78 GBP}'),
            ('    Assets:Foo 100.00 USD  {{}}', None, '    Assets:Foo 100.00 USD'),
            ('    Assets:Foo 100.00 USD  {{12.34 GBP}}', models.CostSpec.from_value(_D('56.78'), None, 'EUR'), '    Assets:Foo 100.00 USD  {56.78 EUR}'),
        ],
    )
    def test_set_raw_cost(self, text: str, cost: Optional[models.CostSpec], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        posting.raw_cost = cost
        assert posting.raw_cost is cost
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,price,expected_text', [
            ('    Assets:Foo 100.00 USD', None, '    Assets:Foo 100.00 USD'),
            ('    Assets:Foo 100.00 USD', models.TotalPrice.from_value(_D('12.34'), 'GBP'), '    Assets:Foo 100.00 USD @@ 12.34 GBP'),
            ('    Assets:Foo 100.00 USD  @ 1.25 GBP', None, '    Assets:Foo 100.00 USD'),
            ('    Assets:Foo 100.00 USD  @@ 80.00 GBP', models.UnitPrice.from_value(_D('1.00'), 'EUR'), '    Assets:Foo 100.00 USD  @ 1.00 EUR'),
        ],
    )
    def test_set_raw_price(self, text: str, price: Optional[models.PriceAnnotation], expected_text: str) -> None:
        posting = self.parser.parse(text, models.Posting)
        posting.raw_price = price
        assert posting.raw_price is price
        assert self.print_model(posting) == expected_text

    @pytest.mark.parametrize(
        'text,flag,account,number,currency,cost,price', _constructor_testcases(),
    )
    def test_from_children(
            self,
            text: str,
            flag: Optional[str],
            account: str,
            number: Optional[decimal.Decimal],
            currency: Optional[str],
            cost: Optional[models.CostSpec],
            price: Optional[models.PriceAnnotation],
    ) -> None:
        raw_indent = models.Indent.from_value(' ' * 4)
        raw_flag = models.PostingFlag.from_value(flag) if flag is not None else None
        raw_account = models.Account.from_value(account)
        raw_number = models.NumberExpr.from_value(number) if number is not None else None
        raw_currency = models.Currency.from_value(currency) if currency is not None else None
        posting = models.Posting.from_children(
            raw_account, raw_number, raw_currency, indent=raw_indent, flag=raw_flag, cost=cost, price=price)
        assert posting.raw_indent is raw_indent
        assert posting.indent == ' ' * 4
        assert posting.raw_flag is raw_flag
        assert posting.flag == flag
        assert posting.raw_account is raw_account
        assert posting.account == account
        assert posting.raw_number is raw_number
        assert posting.number == number
        assert posting.raw_currency is raw_currency
        assert posting.currency == currency
        assert posting.raw_cost is cost
        assert posting.raw_price is price
        assert self.print_model(posting) == text

    @pytest.mark.parametrize(
        'text,flag,account,number,currency,cost,price', _constructor_testcases(),
    )
    def test_from_value(
            self,
            text: str,
            flag: Optional[str],
            account: str,
            number: Optional[decimal.Decimal],
            currency: Optional[str],
            cost: Optional[models.CostSpec],
            price: Optional[models.PriceAnnotation],
    ) -> None:
        posting = models.Posting.from_value(
            account, number, currency, cost=cost, price=price, flag=flag)
        assert posting.indent == ' ' * 4
        assert posting.flag == flag
        assert posting.account == account
        assert posting.number == number
        assert posting.currency == currency
        assert posting.raw_cost is cost
        assert posting.raw_price is price
        assert self.print_model(posting) == text
