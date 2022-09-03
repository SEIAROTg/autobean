
from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base


class TestPopmeta(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,key', [
            ('popmeta foo:', 'foo'),
            ('popmeta\t foo:', 'foo'),
        ],
    )
    def test_parse_success(self, text: str, key: str) -> None:
        popmeta = self.parser.parse(text, models.Popmeta)
        assert popmeta.raw_key.value == key
        assert self.print_model(popmeta) == text
        self.check_deepcopy_tree(popmeta)
        self.check_reattach_tree(popmeta)

    @pytest.mark.parametrize(
        'text', [
            'popMeta foo:',
            'popmeta foo',
            'popmeta ',
            '    popmeta foo:',
            'popmeta foo: 123',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse(text, models.Popmeta)

    def test_set_raw_key(self) -> None:
        popmeta = self.parser.parse('popmeta  foo:', models.Popmeta)
        new_key = models.MetaKey.from_value('bar')
        popmeta.raw_key = new_key
        assert popmeta.raw_key is new_key
        assert self.print_model(popmeta) == 'popmeta  bar:'

    def test_set_key(self) -> None:
        popmeta = self.parser.parse('popmeta  foo:', models.Popmeta)
        assert popmeta.key == 'foo'
        popmeta.key = 'bar'
        assert popmeta.key == 'bar'
        assert self.print_model(popmeta) == 'popmeta  bar:'

    def test_from_children(self) -> None:
        popmeta = models.Popmeta.from_children(models.MetaKey.from_value('foo'))
        assert popmeta.raw_key.value == 'foo'
        assert self.print_model(popmeta) == 'popmeta foo:'
        self.check_consistency(popmeta)

    def test_from_value(self) -> None:
        popmeta = models.Popmeta.from_value('foo')
        assert popmeta.raw_key.value == 'foo'
        assert self.print_model(popmeta) == 'popmeta foo:'
        self.check_consistency(popmeta)
