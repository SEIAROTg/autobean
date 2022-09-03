from lark import exceptions
import pytest
from autobean.refactor import models
from .. import base


class TestNull(base.BaseTestModel):

    def test_parse_success(self) -> None:
        token = self.parser.parse_token('NULL', models.Null)
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
            self.parser.parse_token(text, models.Null)
