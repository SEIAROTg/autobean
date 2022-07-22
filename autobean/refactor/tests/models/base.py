import copy
import inspect
import io
from typing import Any, Iterable, Optional
import pytest
from autobean.refactor import parser as parser_lib
from autobean.refactor import printer
from autobean.refactor.models import raw_models


def _get_comparable_properties(model: raw_models.RawModel) -> dict[str, Any]:
    ret = {}
    for key, value in inspect.getmembers(model):
        if key.startswith('_') or key in ('token_store', 'store_handle', 'tokens'):
            continue
        if callable(value) or value is model:
            continue
        ret[key] = value
    return ret


def _check_copy_eq(
        a: Any,
        b: Any,
        expected_token_store: Optional[raw_models.TokenStore],
        token_index_offset: int = 0) -> None:
    assert type(a) is type(b)
    if isinstance(a, raw_models.RawModel):
        assert a is not b
        assert b.token_store is expected_token_store
        if isinstance(a, raw_models.RawTokenModel) and a.token_store:
            assert a.token_store.get_index(a) + token_index_offset == b.token_store.get_index(b)
        a_props = _get_comparable_properties(a)
        b_props = _get_comparable_properties(b)
        assert a_props.keys() == b_props.keys()
        for key, a_value in a_props.items():
            b_value = b_props[key]
            _check_copy_eq(a_value, b_value, expected_token_store, token_index_offset)
    elif isinstance(a, Iterable) and not isinstance(a, str | bytes):
        a_items, b_items = list(a), list(b)
        assert len(a_items) == len(b_items)
        for a_item, b_item in zip(a_items, b_items):
            _check_copy_eq(a_item, b_item, expected_token_store, token_index_offset)
    else:
        assert a == b


class BaseTestModel:
    @pytest.fixture(autouse=True)
    def _setup_parser(self, parser: parser_lib.Parser) -> None:
        self._parser = parser

    def print_model(self, model: raw_models.RawModel) -> str:
        return printer.print_model(model, io.StringIO()).getvalue()

    def check_deepcopy_token(self, token: raw_models.RawTokenModel) -> None:
        copied = copy.deepcopy(token)
        _check_copy_eq(token, copied, None)

    def check_deepcopy_tree(self, tree: raw_models.RawTreeModel) -> None:
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

    def check_reattach_tree(self, tree: raw_models.RawTreeModel) -> None:
        c = copy.deepcopy(tree)  # make a copy so we don't alter input
        comment_before = raw_models.LineComment.from_raw_text('; before')
        comment_after = raw_models.LineComment.from_raw_text('; after')
        tokens = []
        token_map = {}
        for token in c.token_store:
            new_token = copy.deepcopy(token)
            tokens.append(new_token)
            token_map[id(token)] = new_token
        token_store = raw_models.TokenStore.from_tokens([
            comment_before,
            *tokens,
            comment_after,
        ])
        c.reattach(token_store, raw_models.MappingTokenTransformer(token_map))
        assert c.token_store is token_store
        if tokens:
            assert c.first_token is tokens[0]
            assert c.last_token is tokens[-1]
        _check_copy_eq(tree, c, token_store, 1)

    def check_consistency(self, tree: raw_models.RawTreeModel) -> None:
        for _, prop in _get_comparable_properties(tree).items():
            if isinstance(prop, raw_models.RawTokenModel):
                assert prop.token_store is tree.token_store
            elif isinstance(prop, raw_models.RawTreeModel) and prop is not tree:
                assert prop.token_store is tree.token_store
                self.check_consistency(prop)
