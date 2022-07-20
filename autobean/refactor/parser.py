import copy
import pathlib
from typing import Iterator, Optional, Type, TypeVar
import lark
from lark import exceptions
from lark import lexer
from lark import load_grammar
from autobean.refactor.models import raw_models

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

        token_models: list[raw_models.RawTokenModel] = []
        token_to_model = {}
        for token in tokens:
            token_model = self._token_models[token.type].from_raw_text(token.value)
            token_models.append(token_model)
            token_to_model[token] = token_model

        token_store = raw_models.TokenStore.from_tokens(token_models)
        transformed_tree = self._transform_tree(
            tree,
            target,
            token_store,
            token_to_model)

        return transformed_tree

    def _transform_tree(
            self,
            tree: lark.Tree,
            target: Type[_U],
            token_store: raw_models.TokenStore,
            token_to_model: dict[lark.Token, raw_models.RawTokenModel],
    ) -> _U:
        models = []
        for child in tree.children:
            model: Optional[raw_models.RawModel]
            if child is None:
                model = None
            elif isinstance(child, lark.Token):
                model = token_to_model[child]
            else:
                model = self._transform_tree(
                    child, self._tree_models[child.data], token_store, token_to_model)
            models.append(model)
        return target.from_children(token_store, *models)
