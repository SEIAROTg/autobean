import datetime
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base


class TestNote(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,account,comment', [
            ('2000-01-01 note Assets:Foo "foo"', datetime.date(2000, 1, 1), 'Assets:Foo', 'foo'),
            ('2000-01-01  note  Assets:Foo  "foo"', datetime.date(2000, 1, 1), 'Assets:Foo', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, date: datetime.date, account: str, comment: str) -> None:
        note = self.parser.parse(text, models.Note)
        assert note.raw_date.value == date
        assert note.date == date
        assert note.raw_account.value == account
        assert note.account == account
        assert note.raw_comment.value == comment
        assert note.comment == comment
        self.check_deepcopy_tree(note)
        self.check_reattach_tree(note)

    @pytest.mark.parametrize(
        'text', [
            'note Assets:Foo "foo"',
            '2000-01-01 note Assets:Foo',
            '2000-01-01 note "foo"',
            '2000-01-01 note USD "foo"',
            '2000-01-01 note #tag "foo"',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Note)

    def test_set_raw_date(self) -> None:
        note = self.parser.parse('2000-01-01 note Assets:Foo "foo"', models.Note)
        new_date = models.Date.from_value(datetime.date(2012, 12, 12))
        note.raw_date = new_date
        assert note.raw_date is new_date
        assert self.print_model(note) == '2012-12-12 note Assets:Foo "foo"'

    def test_set_date(self) -> None:
        note = self.parser.parse('2000-01-01  note Assets:Foo "foo"', models.Note)
        assert note.date == datetime.date(2000, 1, 1)
        note.date = datetime.date(2012, 12, 12)
        assert note.date == datetime.date(2012, 12, 12)
        assert self.print_model(note) == '2012-12-12  note Assets:Foo "foo"'

    def test_set_raw_account(self) -> None:
        note = self.parser.parse('2000-01-01 note  Assets:Foo  "foo"', models.Note)
        new_account = models.Account.from_value('Assets:Bar')
        note.raw_account = new_account
        assert note.raw_account is new_account
        assert self.print_model(note) == '2000-01-01 note  Assets:Bar  "foo"'

    def test_set_account(self) -> None:
        note = self.parser.parse('2000-01-01 note  Assets:Foo  "foo"', models.Note)
        assert note.account == 'Assets:Foo'
        note.account = 'Assets:Bar'
        assert note.account == 'Assets:Bar'
        assert self.print_model(note) == '2000-01-01 note  Assets:Bar  "foo"'

    def test_set_raw_comment(self) -> None:
        note = self.parser.parse('2000-01-01 note Assets:Foo  "foo"', models.Note)
        new_comment = models.EscapedString.from_value('bar')
        note.raw_comment = new_comment
        assert note.raw_comment is new_comment
        assert self.print_model(note) == '2000-01-01 note Assets:Foo  "bar"'

    def test_set_comment(self) -> None:
        note = self.parser.parse('2000-01-01 note Assets:Foo  "foo"', models.Note)
        assert note.comment == 'foo'
        note.comment = 'bar'
        assert note.comment == 'bar'
        assert self.print_model(note) == '2000-01-01 note Assets:Foo  "bar"'

    def test_from_children(self) -> None:
        date = models.Date.from_value(datetime.date(2000, 1, 1))
        account = models.Account.from_value('Assets:Foo')
        comment = models.EscapedString.from_value('foo')
        note = models.Note.from_children(date, account, comment)
        assert note.raw_date is date
        assert note.raw_account is account
        assert note.raw_comment is comment
        assert self.print_model(note) == '2000-01-01 note Assets:Foo "foo"'
        self.check_consistency(note)

    def test_from_value(self) -> None:
        note = models.Note.from_value(
            datetime.date(2000, 1, 1),
            'Assets:Foo',
            'foo')
        assert note.raw_date.value == datetime.date(2000, 1, 1)
        assert note.account == 'Assets:Foo'
        assert note.comment == 'foo'
        assert self.print_model(note) == '2000-01-01 note Assets:Foo "foo"'
        self.check_consistency(note)
