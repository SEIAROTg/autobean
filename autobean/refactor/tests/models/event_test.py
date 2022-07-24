import datetime
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestEvent(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,date,type,description', [
            ('2000-01-01 event "foo" "bar"', datetime.date(2000, 1, 1), 'foo', 'bar'),
            ('2012-12-12  event  "baz"  "qux"', datetime.date(2012, 12, 12), 'baz', 'qux'),
        ],
    )
    def test_parse_success(
            self,
            text: str,
            date: datetime.date,
            type: str,
            description: str,
    ) -> None:
        event = self.easy_parser.parse(text, easy_models.Event)
        assert event.first_token is event.raw_date
        assert event.raw_date.value == date
        assert event.date == date
        assert event.raw_type.value == type
        assert event.type == type
        assert event.raw_description.value == description
        assert event.description == description
        assert event.last_token is event.raw_description
        self.check_deepcopy_tree(event)
        self.check_reattach_tree(event)

    @pytest.mark.parametrize(
        'text', [
            '2000-01-01 Event "foo" "bar"',
            '2000-01-01 event "foo"',
            '2000-01-01 event "foo" "bar" "baz"',
            'event "foo" "bar"',
            '2000-01-01 event',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.raw_parser.parse(text, raw_models.Event)

    def test_set_raw_date(self) -> None:
        event = self.raw_parser.parse('2000-01-01  event "foo" "bar"', raw_models.Event)
        new_date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        event.raw_date = new_date
        assert event.raw_date is new_date
        assert self.print_model(event) == '2012-12-12  event "foo" "bar"'

    def test_set_date(self) -> None:
        event = self.easy_parser.parse('2000-01-01  event "foo" "bar"', easy_models.Event)
        assert event.date == datetime.date(2000, 1, 1)
        event.date = datetime.date(2012, 12, 12)
        assert event.date == datetime.date(2012, 12, 12)
        assert self.print_model(event) == '2012-12-12  event "foo" "bar"'

    def test_set_raw_type(self) -> None:
        event = self.raw_parser.parse('2000-01-01 event  "foo"  "bar"', raw_models.Event)
        new_type = raw_models.EscapedString.from_value('baz')
        event.raw_type = new_type
        assert event.raw_type is new_type
        assert self.print_model(event) == '2000-01-01 event  "baz"  "bar"'

    def test_set_type(self) -> None:
        event = self.easy_parser.parse('2000-01-01 event  "foo"  "bar"', easy_models.Event)
        event.type = 'baz'
        assert event.type == 'baz'
        assert self.print_model(event) == '2000-01-01 event  "baz"  "bar"'

    def test_set_raw_description(self) -> None:
        event = self.raw_parser.parse('2000-01-01 event "foo"  "bar"', raw_models.Event)
        new_description = raw_models.EscapedString.from_value('baz')
        event.raw_description = new_description
        assert event.raw_description is new_description
        assert self.print_model(event) == '2000-01-01 event "foo"  "baz"'

    def test_set_description(self) -> None:
        event = self.easy_parser.parse('2000-01-01 event "foo"  "bar"', easy_models.Event)
        event.description = 'baz'
        assert event.description == 'baz'
        assert self.print_model(event) == '2000-01-01 event "foo"  "baz"'

    def test_from_children(self) -> None:
        date = raw_models.Date.from_value(datetime.date(2012, 12, 12))
        type = raw_models.EscapedString.from_value('foo')
        description = raw_models.EscapedString.from_value('bar')
        event = easy_models.Event.from_children(date, type, description)
        assert event.raw_date is date
        assert event.raw_type is type
        assert event.raw_description is description
        assert event.date == datetime.date(2012, 12, 12)
        assert event.type == 'foo'
        assert event.description == 'bar'
        assert self.print_model(event) == '2012-12-12 event "foo" "bar"'

    def test_from_value(self) -> None:
        event = easy_models.Event.from_value(datetime.date(2012, 12, 12), 'foo', 'bar')
        assert event.date == datetime.date(2012, 12, 12)
        assert event.type == 'foo'
        assert event.description == 'bar'
        assert self.print_model(event) == '2012-12-12 event "foo" "bar"'
