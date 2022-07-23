import datetime
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestPad(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,account,source_account', [
            ('2000-01-01 pad Assets:Foo Assets:Bar', datetime.date(2000, 1, 1), 'Assets:Foo', 'Assets:Bar'),
            ('2012-12-12  pad  Assets:Baz  Assets:Qux', datetime.date(2012, 12, 12), 'Assets:Baz', 'Assets:Qux'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            account: str,
            source_account: str,
    ) -> None:
        pad = self._parser.parse(text, easy_models.Pad)
        assert pad.first_token is pad.raw_date
        assert pad.raw_date.value == date
        assert pad.date == date
        assert pad.raw_account.value == account
        assert pad.account == account
        assert pad.raw_source_account.value == source_account
        assert pad.source_account == source_account
        assert pad.last_token is pad.raw_source_account
        self.check_deepcopy_tree(pad)
        self.check_reattach_tree(pad)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 Pad Assets:Foo Assets:Bar',
            '2000-01-01 pad Assets:Foo',
            '2000-01-01 pad Assets:Foo Assets:Bar Assets:Baz',
            'pad Assets:Foo Assets:Bar',
            '2000-01-01 pad',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Pad)

    def test_set_raw_date(self) -> None:
        pad = self._parser.parse('2000-01-01  pad Assets:Foo Assets:Bar', raw_models.Pad)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        pad.raw_date = new_date
        assert pad.raw_date is new_date
        assert self.print_model(pad) == '2012-12-12  pad Assets:Foo Assets:Bar'

    def test_set_date(self) -> None:
        pad = self._parser.parse('2000-01-01  pad Assets:Foo Assets:Bar', easy_models.Pad)
        assert pad.date == datetime.date(2000, 1, 1)
        pad.date = datetime.date(2012, 12, 12)
        assert pad.date == datetime.date(2012, 12, 12)
        assert self.print_model(pad) == '2012-12-12  pad Assets:Foo Assets:Bar'

    def test_set_raw_account(self) -> None:
        pad = self._parser.parse('2000-01-01 pad  Assets:Foo  Assets:Bar', raw_models.Pad)
        new_account = raw_models.Account.from_value('Assets:Baz')
        pad.raw_account = new_account
        assert pad.raw_account is new_account
        assert self.print_model(pad) == '2000-01-01 pad  Assets:Baz  Assets:Bar'

    def test_set_account(self) -> None:
        pad = self._parser.parse('2000-01-01 pad  Assets:Foo  Assets:Bar', easy_models.Pad)
        pad.account = 'Assets:Baz'
        assert pad.account == 'Assets:Baz'
        assert self.print_model(pad) == '2000-01-01 pad  Assets:Baz  Assets:Bar'

    def test_set_raw_source_account(self) -> None:
        pad = self._parser.parse('2000-01-01 pad Assets:Foo  Assets:Bar', raw_models.Pad)
        new_source_account = raw_models.Account.from_value('Assets:Baz')
        pad.raw_source_account = new_source_account
        assert pad.raw_source_account is new_source_account
        assert self.print_model(pad) == '2000-01-01 pad Assets:Foo  Assets:Baz'

    def test_set_source_account(self) -> None:
        pad = self._parser.parse('2000-01-01 pad Assets:Foo  Assets:Bar', easy_models.Pad)
        pad.source_account = 'Assets:Baz'
        assert pad.source_account == 'Assets:Baz'
        assert self.print_model(pad) == '2000-01-01 pad Assets:Foo  Assets:Baz'

    def test_from_children(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        account = raw_models.Account.from_value('Assets:Foo')
        source_account = raw_models.Account.from_value('Assets:Bar')
        pad = easy_models.Pad.from_children(date, account, source_account)
        assert pad.raw_date is date
        assert pad.raw_account is account
        assert pad.raw_source_account is source_account
        assert pad.date == datetime.date(2012, 12, 12)
        assert pad.account == 'Assets:Foo'
        assert pad.source_account == 'Assets:Bar'
        assert self.print_model(pad) == '2012-12-12 pad Assets:Foo Assets:Bar'

    def test_from_value(self) -> None:
        pad = easy_models.Pad.from_value(datetime.date(2012, 12, 12), 'Assets:Foo', 'Assets:Bar')
        assert pad.date == datetime.date(2012, 12, 12)
        assert pad.account == 'Assets:Foo'
        assert pad.source_account == 'Assets:Bar'
        assert self.print_model(pad) == '2012-12-12 pad Assets:Foo Assets:Bar'
