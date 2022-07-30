from lark import exceptions
import pytest
from autobean.refactor import models
from . import base


class TestPoptag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,tag', [
            ('poptag #foo', 'foo'),
            ('poptag\t#foo', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, tag: str) -> None:
        poptag = self.parser.parse(text, models.Poptag)
        assert poptag.first_token.raw_text == 'poptag'
        assert poptag.raw_tag.value == tag
        assert poptag.last_token is poptag.raw_tag
        self.check_deepcopy_tree(poptag)
        self.check_reattach_tree(poptag)

    @pytest.mark.parametrize(
        'text', [
            'popTag #foo',
            'poptag foo',
            'poptag ',
            '    poptag #foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Poptag)

    def test_set_raw_tag(self) -> None:
        poptag = self.parser.parse('poptag  #foo', models.Poptag)
        new_tag = models.Tag.from_value('bar')
        poptag.raw_tag = new_tag
        assert poptag.raw_tag is new_tag
        assert self.print_model(poptag) == 'poptag  #bar'

    def test_set_tag(self) -> None:
        poptag = self.parser.parse('poptag  #foo', models.Poptag)
        assert poptag.tag == 'foo'
        poptag.tag = 'bar'
        assert poptag.tag == 'bar'
        assert self.print_model(poptag) == 'poptag  #bar'

    def test_from_children(self) -> None:
        tag = models.Tag.from_value('foo')
        poptag = models.Poptag.from_children(tag)
        assert poptag.raw_tag is tag
        assert self.print_model(poptag) == 'poptag #foo'
        self.check_consistency(poptag)

    def test_from_value(self) -> None:
        poptag = models.Poptag.from_value('foo')
        assert poptag.raw_tag.value == 'foo'
        assert self.print_model(poptag) == 'poptag #foo'
