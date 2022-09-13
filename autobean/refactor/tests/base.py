import copy
import inspect
import io
import itertools
from typing import Any, Iterable, Optional
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor import printer
from autobean.refactor import models


_IGNORED_ATTRIBUTES = {
    'token_store',
    '_token_store',
    'store_handle',
    'tokens',
    '_abc_impl',
    '_is_protocol',
    '_inferred_indent',
    'inferred_indent',
    'raw_spacing_before',
    'spacing_before',
    'raw_spacing_after',
    'spacing_after',
}


def _get_comparable_attributes(model: models.RawModel) -> dict[str, Any]:
    ret = {}
    for key, value in inspect.getmembers(model):
        if key.startswith('__') or key in _IGNORED_ATTRIBUTES:
            continue
        if callable(value) or value is model:
            continue
        ret[key] = value
    return ret


def _check_copy_eq(
        a: Any,
        b: Any,
        expected_token_store: Optional[models.TokenStore],
        token_index_offset: int = 0,
        checked: Optional[set[tuple[int, int]]] = None) -> None:
    assert type(a) is type(b)
    checked = set() if checked is None else checked
    if (id(a), id(b)) in checked:
        return
    checked.add((id(a), id(b)))
    if isinstance(a, models.RawModel):
        assert a is not b
        assert b.token_store is expected_token_store
        if isinstance(a, models.RawTokenModel) and a.token_store:
            assert a.token_store.get_index(a) + token_index_offset == b.token_store.get_index(b)
        a_props = _get_comparable_attributes(a)
        b_props = _get_comparable_attributes(b)
        assert a_props.keys() == b_props.keys()
        for key, a_value in a_props.items():
            b_value = b_props[key]
            _check_copy_eq(a_value, b_value, expected_token_store, token_index_offset, checked)
    elif isinstance(a, Iterable) and not isinstance(a, str | bytes):
        a_items, b_items = list(a), list(b)
        assert len(a_items) == len(b_items)
        for a_item, b_item in zip(a_items, b_items):
            _check_copy_eq(a_item, b_item, expected_token_store, token_index_offset, checked)
    else:
        assert a == b


class BaseTestModel:
    @pytest.fixture(autouse=True)
    def _setup_parser(self, parser: parser_lib.Parser) -> None:
        self.parser = parser

    def print_model(self, model: models.RawModel) -> str:
        return printer.print_model(model, io.StringIO()).getvalue()

    def check_deepcopy_token(self, token: models.RawTokenModel) -> None:
        copied = copy.deepcopy(token)
        _check_copy_eq(token, copied, None)

    def check_deepcopy_tree(self, tree: models.RawTreeModel) -> None:
        copied = copy.deepcopy(tree)
        assert copied.token_store is not None
        assert copied.token_store is not tree.token_store
        assert copied.first_token is copied.token_store.get_first()
        assert copied.last_token is copied.token_store.get_last()
        if tree.first_token and tree.last_token:
            tokens = list(tree.token_store.iter(tree.first_token, tree.last_token))
        else:
            tokens = []
        assert len(tokens) == len(copied.token_store)
        for original_token, copied_token in zip(tokens, copied.token_store):
            assert copied_token.token_store is copied.token_store
            _check_copy_eq(original_token, copied_token, copied.token_store)
        _check_copy_eq(tree, copied, copied.token_store)

    def check_reattach_tree(self, tree: models.RawTreeModel) -> None:
        c = copy.deepcopy(tree)  # make a copy so we don't alter input
        tokens = []
        token_map = {}
        for token in c.token_store:
            new_token = copy.deepcopy(token)
            tokens.append(new_token)
            token_map[id(token)] = new_token
        token_store = models.TokenStore.from_tokens([
            models.BlockComment.from_raw_text('; before'),
            models.Newline.from_default(),
            *tokens,
            models.BlockComment.from_raw_text('; before'),
        ])
        c.reattach(token_store, models.MappingTokenTransformer(token_map))
        assert c.token_store is token_store
        if tokens:
            assert c.first_token is tokens[0]
            assert c.last_token is tokens[-1]
        _check_copy_eq(tree, c, token_store, 2)

    def check_consistency(self, tree: models.RawTreeModel) -> None:
        for _, prop in _get_comparable_attributes(tree).items():
            if isinstance(prop, models.RawTokenModel):
                assert prop.token_store is tree.token_store
            elif isinstance(prop, models.RawTreeModel) and prop is not tree:
                assert prop.token_store is tree.token_store
                self.check_consistency(prop)

    def check_disjoint(self, a: models.RawModel, b: models.RawModel) -> None:
        xs = {id(x) for x in a.tokens}
        ys = {id(y) for y in b.tokens}
        assert not xs & ys

    def assert_iterable_same(self, xs: Iterable[Any], ys: Iterable[Any]) -> None:
        for x, y in itertools.zip_longest(xs, ys):
            if isinstance(x, models.RawModel) or isinstance(y, models.RawModel):
                assert x is y
            else:
                assert x == y
