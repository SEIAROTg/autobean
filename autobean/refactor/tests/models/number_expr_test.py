import decimal
from typing import Literal
from lark import exceptions
import pytest
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models
from . import base


def _addsub_testcases(op: Literal['+', '-']) -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        'left,right,expected', [
            ('12+34*56', 78, f'12+34*56 {op} 78'),
            ('12+34*56', '78', f'12+34*56 {op} 78'),
            ('12+34*56', decimal.Decimal('78.9012345'), f'12+34*56 {op} 78.9012345'),
            ('12+34*56', '78*90', f'12+34*56 {op} 78*90'),
            ('12+34*56', -78, f'12+34*56 {op} -78'),
            ('12+34*56', '78+90', f'12+34*56 {op} (78+90)'),
        ],
    )


def _raddsub_testcases(op: Literal['+', '-']) -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        'left,right,expected', [
            (12, '34*56', f'12 {op} 34*56'),
            (-12, '34*56', f'-12 {op} 34*56'),
            (decimal.Decimal(12), '34*56', f'12 {op} 34*56'),
            (12, '34*56+78', f'12 {op} (34*56+78)'),
        ],
    )


def _muldiv_testcases(op: Literal['*', '/']) -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        'left,right,expected', [
            ('12*34*56', 78, f'12*34*56 {op} 78'),
            ('12*34*56', '78', f'12*34*56 {op} 78'),
            ('12*34*56', -78, f'12*34*56 {op} -78'),
            ('12*34*56', decimal.Decimal('78.9012345'), f'12*34*56 {op} 78.9012345'),
            ('12*34*56', '78*90', f'12*34*56 {op} (78*90)'),
            ('12*34*56', '78+90', f'12*34*56 {op} (78+90)'),
            ('12+34*56', '78', f'(12+34*56) {op} 78'),
            ('12+34*56', '78+90', f'(12+34*56) {op} (78+90)'),
        ],
    )


def _rmuldiv_testcases(op: Literal['*', '/']) -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        'left,right,expected', [
            (12, '34', f'12 {op} 34'),
            (-12, '34', f'-12 {op} 34'),
            (decimal.Decimal(12), '34', f'12 {op} 34'),
            (12, '34*56', f'12 {op} (34*56)'),
            (12, '34*56+78', f'12 {op} (34*56+78)'),
        ],
    )


def _negpos_testcases(op: Literal['+', '-']) -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        'inner,expected', [
            ('0', f'{op}0'),
            ('12.34', f'{op}12.34'),
            ('-12.34', f'{op}-12.34'),
            ('+12.34', f'{op}+12.34'),
            ('12+34', f'{op}(12+34)'),
            ('12*34', f'{op}(12*34)'),
        ],
    )


class TestNumberExpr(base.BaseTestModel):

    @pytest.mark.parametrize(
        'text,value', [
            ('1234', decimal.Decimal('1234')),
            ('12.34', decimal.Decimal('12.34')),
            ('(12.34)', decimal.Decimal('12.34')),
            ('((12.34))', decimal.Decimal('12.34')),
            ('12.3456789', decimal.Decimal('12.3456789')),
            ('-12.34', decimal.Decimal('-12.34')),
            ('--12.34', decimal.Decimal('12.34')),
            ('---12.34', decimal.Decimal('-12.34')),
            ('+12.34', decimal.Decimal('12.34')),
            ('++12.34', decimal.Decimal('12.34')),
            ('+++12.34', decimal.Decimal('12.34')),
            ('+-+12.34', decimal.Decimal('-12.34')),
            ('12+34', decimal.Decimal('46')),
            ('12 +\t34', decimal.Decimal('46')),
            ('12-34', decimal.Decimal('-22')),
            ('12*34', decimal.Decimal('408')),
            ('36/24', decimal.Decimal('1.5')),
            ('12+34*56', decimal.Decimal('1916')),
            ('(12+34)*56', decimal.Decimal('2576')),
            ('12+34*56+78', decimal.Decimal('1994')),
            ('-(12+34)', decimal.Decimal('-46')),
            ('-12+34', decimal.Decimal('22')),
        ],
    )
    def test_parse_success(self, text: str, value: decimal.Decimal) -> None:
        expr = self._parser.parse(text, raw_models.NumberExpr)
        assert self.print_model(expr) == text
        assert expr.value == value
        self.check_deepcopy_tree(expr)
        self.check_reattach_tree(expr)

    @pytest.mark.parametrize(
        'text', [
            '1^2',
            '((1+2)',
            ')1+2(',
            '(+)1',
            '(1)(2)',
        ],
    )
    def test_parse_failure(self, text: str) -> None:
        with pytest.raises(exceptions.UnexpectedInput):
            self._parser.parse(text, raw_models.NumberExpr)

    def test_set_raw_number_add_expr(self) -> None:
        expr = self._parser.parse('12+34*56+78', raw_models.NumberExpr)
        expr2 = self._parser.parse('48-36/24+12', raw_models.NumberExpr)
        expr.raw_number_add_expr = expr2.raw_number_add_expr
        assert self.print_model(expr) == '48-36/24+12'

    def test_noop_set_raw_number_add_expr(self) -> None:
        expr = self._parser.parse('12+34*56+78', raw_models.NumberExpr)
        expr.raw_number_add_expr = expr.raw_number_add_expr
        assert self.print_model(expr) == '12+34*56+78'

    def test_reuse_active_token(self) -> None:
        expr = self._parser.parse('12+34*56+78', raw_models.NumberExpr)
        expr2 = self._parser.parse('(48-36/24+12)', raw_models.NumberExpr)
        paren_expr = expr2.raw_number_add_expr.raw_operands[0].raw_operands[0]
        assert isinstance(paren_expr, raw_models.NumberParenExpr)
        with pytest.raises(ValueError):
            expr.raw_number_add_expr = paren_expr.raw_inner_expr

    @pytest.mark.parametrize(
        'value,expected', [
            (decimal.Decimal(0), '0'),
            (decimal.Decimal(12), '12'),
            (decimal.Decimal('12.34567'), '12.34567'),
            (decimal.Decimal('-12.34567'), '-12.34567'),
        ],
    )
    def test_from_value(self, value: decimal.Decimal, expected: str) -> None:
        expr = raw_models.NumberExpr.from_value(value)
        assert self.print_model(expr) == expected

    def test_set_value(self) -> None:
        expr = self._parser.parse('12+34*56+78', raw_models.NumberExpr)
        expr.value = decimal.Decimal('-12.34')
        assert self.print_model(expr) == '-12.34'

    def _as_operand(self, value: str | int | decimal.Decimal) -> easy_models.NumberExpr | int | decimal.Decimal:
        if isinstance(value, str):
            return self._parser.parse(value, easy_models.NumberExpr)
        return value

    @_addsub_testcases('+')
    def test_iadd(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        expr += self._as_operand(right)
        assert self.print_model(expr) == expected

    @_addsub_testcases('+')
    def test_add(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        ret = expr + self._as_operand(right)
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_raddsub_testcases('+')
    def test_radd(self, left: str | int | decimal.Decimal, right: str, expected: str) -> None:
        expr = self._parser.parse(right, easy_models.NumberExpr)
        ret = self._as_operand(left) + expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_addsub_testcases('-')
    def test_isub(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        expr -= self._as_operand(right)
        assert self.print_model(expr) == expected

    @_addsub_testcases('-')
    def test_sub(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        ret = expr - self._as_operand(right)
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_raddsub_testcases('-')
    def test_rsub(self, left: str | int | decimal.Decimal, right: str, expected: str) -> None:
        expr = self._parser.parse(right, easy_models.NumberExpr)
        ret = self._as_operand(left) - expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_muldiv_testcases('*')
    def test_imul(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        expr *= self._as_operand(right)
        assert self.print_model(expr) == expected

    @_muldiv_testcases('*')
    def test_mul(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        ret = expr * self._as_operand(right)
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_rmuldiv_testcases('*')
    def test_rmul(self, left: str | int | decimal.Decimal, right: str, expected: str) -> None:
        expr = self._parser.parse(right, easy_models.NumberExpr)
        ret = self._as_operand(left) * expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_muldiv_testcases('/')
    def test_idiv(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        expr /= self._as_operand(right)
        assert self.print_model(expr) == expected

    @_muldiv_testcases('/')
    def test_div(self, left: str, right: str | int | decimal.Decimal, expected: str) -> None:
        expr = self._parser.parse(left, easy_models.NumberExpr)
        ret = expr / self._as_operand(right)
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_rmuldiv_testcases('/')
    def test_rdiv(self, left: str | int | decimal.Decimal, right: str, expected: str) -> None:
        expr = self._parser.parse(right, easy_models.NumberExpr)
        ret = self._as_operand(left) / expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_negpos_testcases('+')
    def test_pos(self, inner: str, expected: str) -> None:
        expr = self._parser.parse(inner, easy_models.NumberExpr)
        ret = +expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @_negpos_testcases('-')
    def test_neg(self, inner: str, expected: str) -> None:
        expr = self._parser.parse(inner, easy_models.NumberExpr)
        ret = -expr
        assert self.print_model(ret) == expected
        assert ret.token_store is not expr.token_store

    @pytest.mark.parametrize(
        'inner,expected', [
            ('12.34', '(12.34)'),
            ('12 +\t34', '(12 +\t34)'),
            ('(12.34)', '((12.34))'),
        ],
    )
    def test_wrap_with_parenthesis(self, inner: str, expected: str) -> None:
        expr = self._parser.parse(inner, easy_models.NumberExpr)
        initial_token_store = expr.token_store
        expr.wrap_with_parenthesis()
        assert self.print_model(expr) == expected
        assert expr.token_store is initial_token_store
