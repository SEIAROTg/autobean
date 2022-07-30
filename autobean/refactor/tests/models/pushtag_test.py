from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestPushtag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,tag', [
            ('pushtag #foo', 'foo'),
            ('pushtag\t#foo', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, tag: str) -> None:
        pushtag = self.parser.parse(text, models.Pushtag)
        assert pushtag.first_token.raw_text == 'pushtag'
        assert pushtag.raw_tag.value == tag
        assert pushtag.last_token is pushtag.raw_tag
        self.check_deepcopy_tree(pushtag)
        self.check_reattach_tree(pushtag)

    @pytest.mark.parametrize(
        'text', [
            'pushTag #foo',
            'pushtag foo',
            'pushtag ',
            '    pushtag #foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Pushtag)

    def test_set_raw_tag(self) -> None:
        pushtag = self.parser.parse('pushtag  #foo', models.Pushtag)
        new_tag = models.Tag.from_value('bar')
        pushtag.raw_tag = new_tag
        assert pushtag.raw_tag is new_tag
        assert self.print_model(pushtag) == 'pushtag  #bar'

    def test_set_tag(self) -> None:
        pushtag = self.parser.parse('pushtag  #foo', models.Pushtag)
        assert pushtag.tag == 'foo'
        pushtag.tag = 'bar'
        assert pushtag.tag == 'bar'
        assert self.print_model(pushtag) == 'pushtag  #bar'

    def test_from_children(self) -> None:
        tag = models.Tag.from_value('foo')
        pushtag = models.Pushtag.from_children(tag)
        assert pushtag.raw_tag is tag
        assert self.print_model(pushtag) == 'pushtag #foo'
        self.check_consistency(pushtag)

    def test_from_value(self) -> None:
        pushtag = models.Pushtag.from_value('foo')
        assert pushtag.raw_tag.value == 'foo'
        assert self.print_model(pushtag) == 'pushtag #foo'
