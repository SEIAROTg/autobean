import pytest
from lark import exceptions
from autobean.refactor import models
from .. import base


class TestIgnored(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text', [
            '* foo',
            '** foo',
            ': foo',
            '# foo',
            'T foo',
            '**',
            '*',
        ],
    )
    def test_parse_success(self, text: str) -> None:
        token = self.parser.parse_token(text, models.Ignored)
        assert token.raw_text == text
        self.check_deepcopy_token(token)

    @pytest.mark.parametrize(
        'text', [
            'txn 123',
            'txn',
            '   * foo',
            '',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self.parser.parse_token(text, models.Ignored)
