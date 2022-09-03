import datetime
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base


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
        event = self.parser.parse(text, models.Event)
        assert event.raw_date.value == date
        assert event.date == date
        assert event.raw_type.value == type
        assert event.type == type
        assert event.raw_description.value == description
        assert event.description == description
        assert self.print_model(event) == text
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
            self.parser.parse(text, models.Event)

    def test_set_raw_date(self) -> None:
        event = self.parser.parse('2000-01-01  event "foo" "bar"', models.Event)
        new_date = models.Date.from_value(datetime.date(2012, 12, 12))
        event.raw_date = new_date
        assert event.raw_date is new_date
        assert self.print_model(event) == '2012-12-12  event "foo" "bar"'

    def test_set_date(self) -> None:
        event = self.parser.parse('2000-01-01  event "foo" "bar"', models.Event)
        assert event.date == datetime.date(2000, 1, 1)
        event.date = datetime.date(2012, 12, 12)
        assert event.date == datetime.date(2012, 12, 12)
        assert self.print_model(event) == '2012-12-12  event "foo" "bar"'

    def test_set_raw_type(self) -> None:
        event = self.parser.parse('2000-01-01 event  "foo"  "bar"', models.Event)
        new_type = models.EscapedString.from_value('baz')
        event.raw_type = new_type
        assert event.raw_type is new_type
        assert self.print_model(event) == '2000-01-01 event  "baz"  "bar"'

    def test_set_type(self) -> None:
        event = self.parser.parse('2000-01-01 event  "foo"  "bar"', models.Event)
        event.type = 'baz'
        assert event.type == 'baz'
        assert self.print_model(event) == '2000-01-01 event  "baz"  "bar"'

    def test_set_raw_description(self) -> None:
        event = self.parser.parse('2000-01-01 event "foo"  "bar"', models.Event)
        new_description = models.EscapedString.from_value('baz')
        event.raw_description = new_description
        assert event.raw_description is new_description
        assert self.print_model(event) == '2000-01-01 event "foo"  "baz"'

    def test_set_description(self) -> None:
        event = self.parser.parse('2000-01-01 event "foo"  "bar"', models.Event)
        event.description = 'baz'
        assert event.description == 'baz'
        assert self.print_model(event) == '2000-01-01 event "foo"  "baz"'

    def test_from_children(self) -> None:
        date = models.Date.from_value(datetime.date(2012, 12, 12))
        type = models.EscapedString.from_value('foo')
        description = models.EscapedString.from_value('bar')
        event = models.Event.from_children(date, type, description)
        assert event.raw_date is date
        assert event.raw_type is type
        assert event.raw_description is description
        assert event.date == datetime.date(2012, 12, 12)
        assert event.type == 'foo'
        assert event.description == 'bar'
        assert self.print_model(event) == '2012-12-12 event "foo" "bar"'

    def test_from_value(self) -> None:
        event = models.Event.from_value(datetime.date(2012, 12, 12), 'foo', 'bar')
        assert event.date == datetime.date(2012, 12, 12)
        assert event.type == 'foo'
        assert event.description == 'bar'
        assert self.print_model(event) == '2012-12-12 event "foo" "bar"'
