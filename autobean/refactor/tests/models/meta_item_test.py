import datetime
import decimal
from typing import Optional
from lark import exceptions
import pytest
from autobean.refactor import models
from . import base

_D = decimal.Decimal


class TestMetaItem(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key,value', [
            ('    foo: Assets:Foo', 'foo', models.Account.from_value('Assets:Foo')),
            ('    foo: 100.00 USD', 'foo', models.Amount.from_value(_D('100.00'), 'USD')),
            ('    foo: TRUE', 'foo', True),
            ('    foo: USD', 'foo', models.Currency.from_value('USD')),
            ('    foo: 2000-01-01', 'foo', datetime.date(2000, 1, 1)),
            ('    foo: "bar"', 'foo', 'bar'),
            ('    foo: NULL', 'foo', models.Null.from_default()),
            ('    foo: 2000 - 01 - 01', 'foo', _D(1998)),
            ('    foo: #bar', 'foo', models.Tag.from_value('bar')),
            ('    foo:', 'foo', None),
            ('    foo: 123', 'foo', _D(123)),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            key: str,
            value: Optional[models.MetaValue],
    ) -> None:
        meta = self.parser.parse(text, models.MetaItem)
        assert meta.key == key
        assert meta.value == value
        assert self.print_model(meta) == text
        self.check_deepcopy_tree(meta)
        self.check_reattach_tree(meta)

    @pytest.mark.parametrize(
        'text', [
            'foo: "bar"',
            '    foo: bar:',
            '    foo: ^bar',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.MetaItem)

    def set_raw_key(self) -> None:
        meta = self.parser.parse('foo: 123', models.MetaItem)
        new_key = models.MetaKey.from_value('bar')
        meta.raw_key = new_key
        assert meta.raw_key is new_key
        assert self.print_model(meta) == 'bar: 123'

    def set_key(self) -> None:
        meta = self.parser.parse('foo: 123', models.MetaItem)
        meta.key = 'bar'
        assert meta.key == 'bar'
        assert self.print_model(meta) == 'bar: 123'

    @pytest.mark.parametrize(
        'text,raw_value,expected', [
            ('    foo:', models.NumberExpr.from_value(_D(123)), '    foo: 123'),
            ('    foo:  Assets:Foo', models.NumberExpr.from_value(_D(123)), '    foo:  123'),
            ('    foo:  Assets:Foo', models.NumberExpr.from_value(_D(123)), '    foo:  123'),
            ('    foo:  Assets:Foo', None, '    foo:'),
        ],
    )
    def test_set_raw_value(self, text: str, raw_value: models.MetaRawValue, expected: str) -> None:
        meta = self.parser.parse(text, models.MetaItem)
        meta.raw_value = raw_value
        assert meta.raw_value is raw_value
        assert self.print_model(meta) == expected

    @pytest.mark.parametrize(
        'text,value,expected', [
            ('    foo:', _D(123), '    foo: 123'),
            ('    foo:  Assets:Foo', _D(123), '    foo:  123'),
            ('    foo:  Assets:Foo', _D(123), '    foo:  123'),
            ('    foo:  Assets:Foo', None, '    foo:'),
        ],
    )
    def test_set_value(self, text: str, value: models.MetaRawValue, expected: str) -> None:
        meta = self.parser.parse(text, models.MetaItem)
        meta.value = value
        assert meta.value == value
        assert self.print_model(meta) == expected

    def test_from_children_with_value(self) -> None:
        indent = models.Whitespace.from_value('    ')
        key = models.MetaKey.from_value('foo')
        value = models.Amount.from_value(_D(123), 'USD')
        meta = models.MetaItem.from_children(indent, key, value)
        assert meta.raw_indent is indent
        assert meta.raw_key is key
        assert meta.raw_value is value
        assert self.print_model(meta) == '    foo: 123 USD'

    def test_from_children_without_value(self) -> None:
        indent = models.Whitespace.from_value('    ')
        key = models.MetaKey.from_value('foo')
        meta = models.MetaItem.from_children(indent, key, None)
        assert meta.raw_indent is indent
        assert meta.raw_key is key
        assert meta.raw_value is None
        assert self.print_model(meta) == '    foo:'

    def test_from_value_with_value(self) -> None:
        meta = models.MetaItem.from_value('foo', 'bar')
        assert meta.indent == '    '
        assert meta.key == 'foo'
        assert meta.value == 'bar'
        assert self.print_model(meta) == '    foo: "bar"'

    def test_from_value_without_value(self) -> None:
        meta = models.MetaItem.from_value('foo', None)
        assert meta.indent == '    '
        assert meta.key == 'foo'
        assert meta.value is None
        assert self.print_model(meta) == '    foo:'
