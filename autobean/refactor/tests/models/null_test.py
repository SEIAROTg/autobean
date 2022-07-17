from lark import exceptions
import pytest
from autobean.refactor.models import raw_models
from . import base


class TestNull(base.BaseTestModel):

    def test_parse_success(self) -> None:
        token = self._parser.parse_token('NULL', raw_models.Null)
        assert token.raw_text == 'NULL'
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            'Null',
            'None',
            'null',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse_token(text, raw_models.Null)
