import datetime
from typing import Optional, Type
import pytest
from autobean.refactor import models
from .. import base


class TestInlineComment(base.BaseTestModel):

    @pytest.mark.parametrize(
        'model_type,text,inline_comment', [
            (models.Close, '2000-01-01 close Assets:Foo  ; foo', 'foo'),
            (models.Close, '2000-01-01 close Assets:Foo', None),
            (models.MetaItem, '  foo: "bar"    ; baz', 'baz'),
            (models.MetaItem, '  foo: "bar"    ', None),
            (models.Posting, '  Assets:Foo  ; foo\n    bar: "baz" ; bar', 'foo'),
            (models.Posting, '  Assets:Foo  \n    bar: "baz" ; bar', None),
            (models.Transaction, '2000-01-01 * ; foo\n Assets:Foo  ; bar\n    bar: "baz" ; baz', 'foo'),
            (models.Transaction, '2000-01-01 * \n Assets:Foo  ; bar\n    bar: "baz" ; baz', None),
        ],
    )
    def test_parse_success(self, model_type: Type[models.RawTreeModel], text: str, inline_comment: models.InlineComment) -> None:
        model = self.parser.parse(text, model_type)
        assert getattr(model, 'inline_comment') == inline_comment
        assert self.print_model(model) == text

    @pytest.mark.parametrize(
        'text,inline_comment,expected_text', [
            ('2000-01-01 close Assets:Foo   ; bar', 'baz', '2000-01-01 close Assets:Foo   ; baz'),
            ('2000-01-01 close Assets:Foo   ; bar', None, '2000-01-01 close Assets:Foo'),
            ('2000-01-01 close Assets:Foo', None, '2000-01-01 close Assets:Foo'),
            ('2000-01-01 close Assets:Foo', 'bar', '2000-01-01 close Assets:Foo ; bar'),
        ],
    )
    def test_set_raw_inline_comment(self, text: str, inline_comment: Optional[str], expected_text: str) -> None:
        close = self.parser.parse(text, models.Close)
        raw_inline_comment = models.InlineComment.from_value(inline_comment) if inline_comment is not None else None
        close.raw_inline_comment = raw_inline_comment
        assert close.raw_inline_comment is raw_inline_comment
        assert close.inline_comment == inline_comment
        assert self.print_model(close) == expected_text

    @pytest.mark.parametrize(
        'text,inline_comment,expected_text', [
            ('2000-01-01 close Assets:Foo   ; bar', 'baz', '2000-01-01 close Assets:Foo   ; baz'),
            ('2000-01-01 close Assets:Foo   ; bar', None, '2000-01-01 close Assets:Foo'),
            ('2000-01-01 close Assets:Foo', None, '2000-01-01 close Assets:Foo'),
            ('2000-01-01 close Assets:Foo', 'bar', '2000-01-01 close Assets:Foo ; bar'),
        ],
    )
    def test_set_value(self, text: str, inline_comment: Optional[str], expected_text: str) -> None:
        close = self.parser.parse(text, models.Close)
        close.inline_comment = inline_comment
        assert close.inline_comment == inline_comment
        assert self.print_model(close) == expected_text

    def test_from_children(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        account = models.Account.from_value('Assets:Foo')
        inline_comment = models.InlineComment.from_value('bar')
        close = models.Close.from_children(date, account, inline_comment=inline_comment)
        assert close.raw_inline_comment is inline_comment
        assert self.print_model(close) == '2000-01-01 close Assets:Foo ; bar'

    def test_from_value(self) -> None:
        close = models.Close.from_value(datetime.date(2000, 1, 1), 'Assets:Foo', inline_comment='bar')
        assert close.inline_comment == 'bar'
        assert self.print_model(close) == '2000-01-01 close Assets:Foo ; bar'
