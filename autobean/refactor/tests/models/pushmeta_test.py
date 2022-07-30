import copy
import decimal
import datetime
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


_SimplifiedValue = Optional[models.MetaValue | decimal.Decimal | datetime.date | str | bool]

# (text, key, raw_value, value)
_Testcase = tuple[str, str, Optional[models.MetaValue], _SimplifiedValue]
_VALID_TESTCASES_FOO: list[_Testcase] = [
    ('pushmeta foo:', 'foo', None, None),
    ('pushmeta foo:  "123"', 'foo', models.EscapedString.from_value('123'), '123'),
    ('pushmeta foo:  Assets:Foo', 'foo', models.Account.from_value('Assets:Foo'), models.Account.from_value('Assets:Foo')),
    ('pushmeta foo:  2020-01-01', 'foo', models.Date.from_value(datetime.date(2020, 1, 1)), datetime.date(2020, 1, 1)),
    ('pushmeta foo:  USD', 'foo', models.Currency.from_value('USD'), models.Currency.from_value('USD')),
    ('pushmeta foo:  #foo', 'foo', models.Tag.from_value('foo'), models.Tag.from_value('foo')),
    ('pushmeta foo:  TRUE', 'foo', models.Bool.from_value(True), True),
    ('pushmeta foo:  NULL', 'foo', models.Null.from_raw_text('NULL'), models.Null.from_raw_text('NULL')),
    ('pushmeta foo:  123', 'foo', models.NumberExpr.from_value(decimal.Decimal(123)), decimal.Decimal(123)),
    ('pushmeta foo:  123 USD', 'foo', models.Amount.from_value(decimal.Decimal(123), 'USD'), models.Amount.from_value(decimal.Decimal(123), 'USD')),
]
_VALID_TESTCASES_BAR: list[_Testcase] = [
    ('pushmeta foo:', 'foo', None, None),
    ('pushmeta foo:  "456"', 'foo', models.EscapedString.from_value('456'), '456'),
    ('pushmeta foo:  Assets:Bar', 'foo', models.Account.from_value('Assets:Bar'), models.Account.from_value('Assets:Bar')),
    ('pushmeta foo:  2012-12-12', 'foo', models.Date.from_value(datetime.date(2012, 12, 12)), datetime.date(2012, 12, 12)),
    ('pushmeta foo:  EUR', 'foo', models.Currency.from_value('EUR'), models.Currency.from_value('EUR')),
    ('pushmeta foo:  #bar', 'foo', models.Tag.from_value('bar'), models.Tag.from_value('bar')),
    ('pushmeta foo:  FALSE', 'foo', models.Bool.from_value(False), False),
    ('pushmeta foo:  NULL', 'foo', models.Null.from_raw_text('NULL'), models.Null.from_raw_text('NULL')),
    ('pushmeta foo:  456', 'foo', models.NumberExpr.from_value(decimal.Decimal(456)), decimal.Decimal(456)),
    ('pushmeta foo:  456 EUR', 'foo', models.Amount.from_value(decimal.Decimal(456), 'EUR'), models.Amount.from_value(decimal.Decimal(456), 'EUR')),
]
_VALID_TESTCASES_BAR_ROTATED = [
    *_VALID_TESTCASES_BAR[1:],
    _VALID_TESTCASES_BAR[0],
]


class TestPushmeta(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key,raw_value,value', _VALID_TESTCASES_FOO + [
            ('pushmeta\t foo:', 'foo', None, None),
        ],
    )
    def test_parse_success(self, text: str, key: str, raw_value: models.MetaValue, value: _SimplifiedValue) -> None:
        del value  # unused
        pushmeta = self.parser.parse(text, models.Pushmeta)
        assert pushmeta.raw_key.value == key
        assert pushmeta.raw_value == raw_value
        assert self.print_model(pushmeta) == text
        self.check_deepcopy_tree(pushmeta)
        self.check_reattach_tree(pushmeta)
        assert self.print_model(pushmeta) == text

    @pytest.mark.parametrize(
        'text', [
            'pushMeta foo:',
            'pushmeta foo',
            'pushmeta ',
            '    pushmeta foo:',
            'pushmeta foo: ^foo',
            'pushmeta foo: *',
            'pushmeta foo: USD 123',
            'pushmeta foo: 123 456',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Pushmeta)

    def test_set_raw_key(self) -> None:
        pushmeta = self.parser.parse('pushmeta  foo:', models.Pushmeta)
        new_key = models.MetaKey.from_value('bar')
        pushmeta.raw_key = new_key
        assert pushmeta.raw_key is new_key
        assert self.print_model(pushmeta) == 'pushmeta  bar:'

    def test_set_key(self) -> None:
        pushmeta = self.parser.parse('pushmeta  foo:', models.Pushmeta)
        assert pushmeta.key == 'foo'
        pushmeta.key = 'bar'
        assert pushmeta.key == 'bar'
        assert self.print_model(pushmeta) == 'pushmeta  bar:'

    @pytest.mark.parametrize(
        'before,after', [
            *zip(_VALID_TESTCASES_FOO, _VALID_TESTCASES_BAR),
            *zip(_VALID_TESTCASES_FOO, _VALID_TESTCASES_BAR_ROTATED),
        ]
    )
    def test_set_raw_value(self, before: _Testcase, after: _Testcase) -> None:
        text_before, _, raw_value, _ = before
        text_after, _, expected_raw_value, _ = after
        pushmeta = self.parser.parse(text_before, models.Pushmeta)
        expected = self.parser.parse(text_after, models.Pushmeta)
        new_value = copy.deepcopy(expected.raw_value)
        pushmeta.raw_value = new_value
        assert pushmeta.raw_value is new_value
        assert pushmeta.raw_value == expected_raw_value
        if raw_value is not None:  # whitespaces may not match if value is created
            assert self.print_model(pushmeta) == text_after

    @pytest.mark.parametrize(
        'before,after', [
            *zip(_VALID_TESTCASES_FOO, _VALID_TESTCASES_BAR),
            *zip(_VALID_TESTCASES_FOO, _VALID_TESTCASES_BAR_ROTATED),
        ]
    )
    def test_set_value(self, before: _Testcase, after: _Testcase) -> None:
        text_before, _, _, value = before
        text_after, _, _, expected_value = after
        pushmeta = self.parser.parse(text_before, models.Pushmeta)
        assert pushmeta.value == value
        expected = self.parser.parse(text_after, models.Pushmeta)
        pushmeta.value = copy.deepcopy(expected.value)
        assert pushmeta.raw_value == expected.raw_value
        assert pushmeta.value == expected_value
        if value is not None:  # whitespaces may not match if value is created
            assert self.print_model(pushmeta) == text_after

    def test_from_children_with_value(self) -> None:
        pushmeta = models.Pushmeta.from_children(
            models.MetaKey.from_value('foo'),
            models.EscapedString.from_value('bar'),
        )
        assert pushmeta.raw_key.value == 'foo'
        assert pushmeta.raw_value == models.EscapedString.from_value('bar')
        assert self.print_model(pushmeta) == 'pushmeta foo: "bar"'
        self.check_consistency(pushmeta)

    def test_from_children_without_value(self) -> None:
        pushmeta = models.Pushmeta.from_children(models.MetaKey.from_value('foo'), None)
        assert pushmeta.raw_key.value == 'foo'
        assert pushmeta.raw_value is None
        assert self.print_model(pushmeta) == 'pushmeta foo:'
        self.check_consistency(pushmeta)
