import datetime
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestCommodity(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,currency', [
            ('2000-01-01 commodity USD', datetime.date(2000, 1, 1), 'USD'),
            ('2012-12-12  commodity  EUR', datetime.date(2012, 12, 12), 'EUR'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            currency: str,
    ) -> None:
        commodity = self._parser.parse(text, easy_models.Commodity)
        assert commodity.first_token is commodity.raw_date
        assert commodity.raw_date.value == date
        assert commodity.date == date
        assert commodity.raw_currency.value == currency
        assert commodity.currency == currency
        assert commodity.last_token is commodity.raw_currency
        self.check_deepcopy_tree(commodity)
        self.check_reattach_tree(commodity)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 commodIty USD',
            'commodity USD',
            '2000-01-01 commodity',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Commodity)

    def test_set_raw_date(self) -> None:
        commodity = self._parser.parse('2000-01-01  commodity USD', raw_models.Commodity)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        commodity.raw_date = new_date
        assert commodity.raw_date is new_date
        assert self.print_model(commodity) == '2012-12-12  commodity USD'

    def test_set_date(self) -> None:
        commodity = self._parser.parse('2000-01-01  commodity USD', easy_models.Commodity)
        assert commodity.date == datetime.date(2000, 1, 1)
        commodity.date = datetime.date(2012, 12, 12)
        assert commodity.date == datetime.date(2012, 12, 12)
        assert self.print_model(commodity) == '2012-12-12  commodity USD'

    def test_set_raw_currency(self) -> None:
        commodity = self._parser.parse('2000-01-01  commodity USD', raw_models.Commodity)
        new_currency = raw_models.Currency.from_value('EUR')
        commodity.raw_currency = new_currency
        assert commodity.raw_currency is new_currency
        assert self.print_model(commodity) == '2000-01-01  commodity EUR'

    def test_set_currency(self) -> None:
        commodity = self._parser.parse('2000-01-01  commodity USD', easy_models.Commodity)
        assert commodity.currency == 'USD'
        commodity.currency = 'EUR'
        assert commodity.currency == 'EUR'
        assert self.print_model(commodity) == '2000-01-01  commodity EUR'

    def test_from_children(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        currency = raw_models.Currency.from_value('EUR')
        commodity = easy_models.Commodity.from_children(date, currency)
        assert commodity.raw_date is date
        assert commodity.raw_currency is currency
        assert commodity.date == datetime.date(2012, 12, 12)
        assert commodity.currency == 'EUR'
        assert self.print_model(commodity) == '2012-12-12 commodity EUR'

    def test_from_value(self) -> None:
        commodity = easy_models.Commodity.from_value(datetime.date(2012, 12, 12), 'EUR')
        assert commodity.date == datetime.date(2012, 12, 12)
        assert commodity.currency == 'EUR'
        assert self.print_model(commodity) == '2012-12-12 commodity EUR'
