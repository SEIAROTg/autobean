import datetime
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestQuery(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,type,query_string', [
            ('2000-01-01 query "foo" "bar"', datetime.date(2000, 1, 1), 'foo', 'bar'),
            ('2012-12-12  query  "baz"  "qux"', datetime.date(2012, 12, 12), 'baz', 'qux'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            type: str,
            query_string: str,
    ) -> None:
        query = self.easy_parser.parse(text, easy_models.Query)
        assert query.first_token is query.raw_date
        assert query.raw_date.value == date
        assert query.date == date
        assert query.raw_name.value == type
        assert query.name == type
        assert query.raw_query_string.value == query_string
        assert query.query_string == query_string
        assert query.last_token is query.raw_query_string
        self.check_deepcopy_tree(query)
        self.check_reattach_tree(query)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 Query "foo" "bar"',
            '2000-01-01 query "foo"',
            '2000-01-01 query "foo" "bar" "baz"',
            'query "foo" "bar"',
            '2000-01-01 query',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse(text, raw_models.Query)

    def test_set_raw_date(self) -> None:
        query = self.raw_parser.parse('2000-01-01  query "foo" "bar"', raw_models.Query)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        query.raw_date = new_date
        assert query.raw_date is new_date
        assert self.print_model(query) == '2012-12-12  query "foo" "bar"'

    def test_set_date(self) -> None:
        query = self.easy_parser.parse('2000-01-01  query "foo" "bar"', easy_models.Query)
        assert query.date == datetime.date(2000, 1, 1)
        query.date = datetime.date(2012, 12, 12)
        assert query.date == datetime.date(2012, 12, 12)
        assert self.print_model(query) == '2012-12-12  query "foo" "bar"'

    def test_set_raw_name(self) -> None:
        query = self.raw_parser.parse('2000-01-01 query  "foo"  "bar"', raw_models.Query)
        new_type = raw_models.EscapedString.from_value('baz')
        query.raw_name = new_type
        assert query.raw_name is new_type
        assert self.print_model(query) == '2000-01-01 query  "baz"  "bar"'

    def test_set_type(self) -> None:
        query = self.easy_parser.parse('2000-01-01 query  "foo"  "bar"', easy_models.Query)
        query.name = 'baz'
        assert query.name == 'baz'
        assert self.print_model(query) == '2000-01-01 query  "baz"  "bar"'

    def test_set_raw_query_string(self) -> None:
        query = self.raw_parser.parse('2000-01-01 query "foo"  "bar"', raw_models.Query)
        new_query_string = raw_models.EscapedString.from_value('baz')
        query.raw_query_string = new_query_string
        assert query.raw_query_string is new_query_string
        assert self.print_model(query) == '2000-01-01 query "foo"  "baz"'

    def test_set_query_string(self) -> None:
        query = self.easy_parser.parse('2000-01-01 query "foo"  "bar"', easy_models.Query)
        query.query_string = 'baz'
        assert query.query_string == 'baz'
        assert self.print_model(query) == '2000-01-01 query "foo"  "baz"'

    def test_from_children(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        type = raw_models.EscapedString.from_value('foo')
        query_string = raw_models.EscapedString.from_value('bar')
        query = easy_models.Query.from_children(date, type, query_string)
        assert query.raw_date is date
        assert query.raw_name is type
        assert query.raw_query_string is query_string
        assert query.date == datetime.date(2012, 12, 12)
        assert query.name == 'foo'
        assert query.query_string == 'bar'
        assert self.print_model(query) == '2012-12-12 query "foo" "bar"'

    def test_from_value(self) -> None:
        query = easy_models.Query.from_value(datetime.date(2012, 12, 12), 'foo', 'bar')
        assert query.date == datetime.date(2012, 12, 12)
        assert query.name == 'foo'
        assert query.query_string == 'bar'
        assert self.print_model(query) == '2012-12-12 query "foo" "bar"'
