import copy
import pathlib
from typing import Iterator, Optional, Type, TypeVar
import lark
from lark import exceptions
from lark import lexer
from lark import load_grammar
from autobean.refactor.models import raw_models
from autobean.refactor.models.raw_models import internal

_T = TypeVar('_T', bound=raw_models.RawTokenModel)
_U = TypeVar('_U', bound=raw_models.RawTreeModel)


with open(pathlib.Path(__file__).parent / 'beancount.lark') as f:
    _GRAMMAR, _ = load_grammar.load_grammar(
        grammar=f.read(),
        source=f.name,
        import_paths=[],
        global_keep_all_tokens=False)
    _IGNORED_TOKENS = frozenset(_GRAMMAR.ignore)
    _GRAMMAR.ignore.clear()


class PostLex(lark.lark.PostLex):
    always_accept = _IGNORED_TOKENS

    def process(self, stream: Iterator[lark.Token]) -> Iterator[lark.Token]:
        return stream


class Parser:
    _lark: lark.Lark
    _token_models: dict[str, Type[raw_models.RawTokenModel]]
    _tree_models: dict[str, Type[raw_models.RawTreeModel]]

    def __init__(
            self,
            token_models: list[Type[raw_models.RawTokenModel]],
            tree_models: list[Type[raw_models.RawTreeModel]],
    ):
        start = ['_unused'] + [model.RULE for model in tree_models]
        self._lark = lark.Lark(
            _GRAMMAR, lexer='contextual', parser='lalr', postlex=PostLex(), start=start)
        self._token_models = {model.RULE: model for model in token_models}
        self._tree_models = {model.RULE: model for model in tree_models}

    def parse_token(self, text: str, target: Type[_T]) -> _T:
        """Parses one token.

        This is a separate method to ease typing and support ignored tokens.
        """
        lexer_conf = copy.deepcopy(self._lark.parser.lexer_conf)
        lexer_conf.terminals = [lexer_conf.terminals_by_name[target.RULE]]
        basic_lexer = lexer.BasicLexer(lexer_conf)
        lexer_thread = lexer.LexerThread.from_text(basic_lexer, text)
        tokens = list(lexer_thread.lex(None))
        if not tokens:
            raise exceptions.UnexpectedToken(
                lark.Token('$END', '', 0, 1, 1), {target.RULE})
        if tokens[0].type != target.RULE:
            raise exceptions.UnexpectedToken(tokens[0], {target.RULE})
        if len(tokens) > 1:
            raise exceptions.UnexpectedToken(tokens[1], {'$END'})
        return target.from_raw_text(tokens[0].value)

    def parse(self, text: str, target: Type[_U]) -> _U:
        parser = self._lark.parse_interactive(text=text, start=target.RULE)
        tokens = []

        for token in parser.lexer_thread.lex(parser.parser_state):
            tokens.append(token)
            if token.type in _IGNORED_TOKENS:
                continue
            parser.feed_token(token)
        tree = parser.feed_eof()

        return ModelBuilder(tokens, self._token_models, self._tree_models).build(tree, target)


class ModelBuilder:
    def __init__(self, tokens: list[lark.Token], token_models: dict[str, Type[raw_models.RawTokenModel]], tree_models: dict[str, Type[raw_models.RawTreeModel]]):
        self._tokens = tokens
        self._token_models = token_models 
        self._tree_models = tree_models
        self._built_tokens: list[raw_models.RawTokenModel] = []
        self._token_to_index = {id(token): i for i, token in enumerate(tokens)}
        self._cursor = 0
        self._right_floating_placeholders: list[raw_models.Placeholder] = []
        self._token_store = raw_models.TokenStore.from_tokens([])

    def _fix_gap(self, cursor: int) -> None:
        for token in self._tokens[self._cursor:cursor]:
            self._built_tokens.append(self._token_models[token.type].from_raw_text(token.value))
        self._cursor = cursor
        self._built_tokens.extend(self._right_floating_placeholders)
        self._right_floating_placeholders.clear()

    def _add_placeholder(self, floating: internal.Floating) -> raw_models.Placeholder:
        placeholder = raw_models.Placeholder.from_default()
        if floating == internal.Floating.RIGHT:
            self._right_floating_placeholders.append(placeholder)
        elif floating == internal.Floating.LEFT:
            if self._right_floating_placeholders:
                raise ValueError('Floating direction cannot be satisified.')
            self._built_tokens.append(placeholder)
        else:
            assert False
        return placeholder

    def _add_token(self, token: lark.Token) -> raw_models.RawTokenModel:
        self._fix_gap(self._token_to_index[id(token)])
        built_token = self._token_models[token.type].from_raw_text(token.value)
        self._built_tokens.append(built_token)
        self._cursor += 1
        return built_token

    def _add_tree(self, tree: lark.Tree) -> raw_models.RawTreeModel:
        model_type = self._tree_models[tree.data]
        fields = internal.list_fields(model_type)
        if fields:
            assert len(tree.children) == len(fields)
            children = []
            for child, field in zip(tree.children, fields):
                if isinstance(field, internal.required_field):
                    children.append(self._add_required_node(child))
                elif isinstance(field, internal.optional_field):
                    children.append(self._add_optional_node(child, field.floating))
                else:
                    assert False
        else:
            children = [self._add_required_node(child) for child in tree.children]
        return model_type.from_parsed_children(self._token_store, *children)

    def _add_required_node(self, node: lark.Token | lark.Tree) -> raw_models.RawModel:
        if isinstance(node, lark.Token):
            return self._add_token(node)
        if isinstance(node, lark.Tree):
            return self._add_tree(node)
        assert False

    def _add_optional_node(self, node: lark.Token | lark.Tree | None, floating: internal.Floating) -> raw_models.RawModel:
        placeholder = self._add_placeholder(floating)
        inner = self._add_required_node(node) if node is not None else None
        if floating == internal.Floating.LEFT:
            return internal.MaybeL(self._token_store, inner, placeholder)
        if floating == internal.Floating.RIGHT:
            return internal.MaybeR(self._token_store, inner, placeholder)
        assert False

    def build(self, tree: lark.Tree, model_type: Type[_U]) -> _U:
        model = self._add_tree(tree)
        self._fix_gap(len(self._tokens))
        self._token_store.insert_after(None, self._built_tokens)
        assert isinstance(model, model_type)
        return model
