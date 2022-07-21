from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


class TestPushtag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,tag', [
            ('pushtag #foo', 'foo'),
            ('pushtag\t#foo', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, tag: str) -> None:
        pushtag = self._parser.parse(text, raw_models.Pushtag)
        assert pushtag.first_token.raw_text == 'pushtag'
        assert pushtag.raw_tag.value == tag
        assert pushtag.last_token is pushtag.raw_tag
        self.check_deepcopy_tree(pushtag)
        self.check_reattach_tree(pushtag)

    @pytest.mark.parametrize(
        'text', [
            'pushtag foo',
            'pushtag ',
            '    pushtag #foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Pushtag)

    def test_set_raw_tag(self) -> None:
        pushtag = self._parser.parse('pushtag  #foo', raw_models.Pushtag)
        new_tag = raw_models.Tag.from_value('bar')
        pushtag.raw_tag = new_tag
        assert pushtag.raw_tag is new_tag
        assert self.print_model(pushtag) == 'pushtag  #bar'

    def test_set_tag(self) -> None:
        pushtag = self._parser.parse('pushtag  #foo', easy_models.Pushtag)
        assert pushtag.tag == 'foo'
        pushtag.tag = 'bar'
        assert pushtag.tag == 'bar'
        assert self.print_model(pushtag) == 'pushtag  #bar'


class TestPoptag(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,tag', [
            ('poptag #foo', 'foo'),
            ('poptag\t#foo', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, tag: str) -> None:
        poptag = self._parser.parse(text, raw_models.Poptag)
        assert poptag.first_token.raw_text == 'poptag'
        assert poptag.raw_tag.value == tag
        assert poptag.last_token is poptag.raw_tag
        self.check_deepcopy_tree(poptag)
        self.check_reattach_tree(poptag)

    @pytest.mark.parametrize(
        'text', [
            'poptag foo',
            'poptag ',
            '    poptag #foo',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.Poptag)

    def test_set_raw_tag(self) -> None:
        poptag = self._parser.parse('poptag  #foo', raw_models.Poptag)
        new_tag = raw_models.Tag.from_value('bar')
        poptag.raw_tag = new_tag
        assert poptag.raw_tag is new_tag
        assert self.print_model(poptag) == 'poptag  #bar'

    def test_set_tag(self) -> None:
        poptag = self._parser.parse('poptag  #foo', easy_models.Poptag)
        assert poptag.tag == 'foo'
        poptag.tag = 'bar'
        assert poptag.tag == 'bar'
        assert self.print_model(poptag) == 'poptag  #bar'
