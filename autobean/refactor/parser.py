import copy
import enum
import pathlib
import re
from typing import Iterable, Iterator, Optional, Type, TypeVar
import lark
from lark import exceptions
from lark import lexer
from lark import load_grammar
from autobean.refactor import models
from autobean.refactor.models import internal

_T = TypeVar('_T', bound=models.RawTokenModel)
_U = TypeVar('_U', bound=models.RawTreeModel)


with open(pathlib.Path(__file__).parent / 'beancount.lark') as f:
    _GRAMMAR, _ = load_grammar.load_grammar(
        grammar=f.read(),
        source=f.name,
        import_paths=[],
        global_keep_all_tokens=False)
    _IGNORED_TOKENS = frozenset(_GRAMMAR.ignore)
    _GRAMMAR.ignore.clear()


class PostLexInline(lark.lark.PostLex):
    always_accept = _IGNORED_TOKENS

    def process(self, stream: Iterator[lark.Token]) -> Iterator[lark.Token]:
        return stream


class PostLex(lark.lark.PostLex):
    _NEWLINE_INDENT_COMMENT_SPLIT_RE = re.compile(r'([\r\n]*)([ \t]*)(;.*)?', re.S)
    _NEWLINE_INDENT_COMMENT = '_NEWLINE_INDENT_COMMENT'
    _NEWLINE = '_NEWLINE'
    _EOL = 'EOL'
    _INDENT = '_INDENT'
    _DEDENT = '_DEDENT'
    _WHITESPACE = 'WHITESPACE'
    _BLOCK_COMMENT = 'BLOCK_COMMENT'

    # Contextual lexer only sees _EOL and will thus reject _NEWLINE by default.
    always_accept = _IGNORED_TOKENS | {_NEWLINE_INDENT_COMMENT}

    def process(self, stream: Iterator[lark.Token]) -> Iterator[lark.Token]:
        indented = False
        token = None
        for token in stream:
            if token.type != self._NEWLINE_INDENT_COMMENT:
                yield token
                continue
            match = self._NEWLINE_INDENT_COMMENT_SPLIT_RE.fullmatch(token.value)
            assert match
            newline_text, indent_text, comment_text = match.groups()
            if newline_text:
                yield lark.Token.new_borrow_pos(self._EOL, '', token)
                yield lark.Token.new_borrow_pos(self._NEWLINE, newline_text, token)
            if indent_text and not indented:
                indented = True
                yield lark.Token.new_borrow_pos(self._INDENT, '', token)
            if comment_text:
                yield lark.Token.new_borrow_pos(self._BLOCK_COMMENT, indent_text + comment_text, token)
            elif indent_text:
                yield lark.Token.new_borrow_pos(self._WHITESPACE, indent_text, token)
            if not indent_text and indented:
                indented = False
                yield lark.Token.new_borrow_pos(self._DEDENT, '', token)
        yield lark.Token(self._EOL, '')
        if indented:
            yield lark.Token(self._DEDENT, '')


class _Floating(enum.Enum):
    LEFT = enum.auto()
    RIGHT = enum.auto()


class Parser:
    _lark: lark.Lark
    _token_models: dict[str, Type[models.RawTokenModel]]
    _tree_models: dict[str, Type[models.RawTreeModel]]

    def __init__(
            self,
            token_models: dict[str, Type[models.RawTokenModel]],
            tree_models: dict[str, Type[models.RawTreeModel]],
    ):
        start = list(tree_models.keys())
        self._lark = lark.Lark(
            _GRAMMAR, lexer='contextual', parser='lalr', postlex=PostLex(), start=start)
        self._lark_inline = lark.Lark(
            _GRAMMAR, lexer='contextual', parser='lalr', postlex=PostLexInline(), start=start)
        self._token_models = token_models
        self._tree_models = tree_models

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

    def parse_inline(self, text: str, target: Type[_U]) -> _U:
        return self._parse(text, target, self._lark_inline)

    def parse(self, text: str, target: Type[_U]) -> _U:
        return self._parse(text, target, self._lark)

    def _parse(self, text: str, target: Type[_U], lark_instance: lark.Lark) -> _U:
        parser = lark_instance.parse_interactive(text=text, start=target.RULE)
        tokens = []
        for token in parser.lexer_thread.lex(parser.parser_state):
            if token.type not in ('_INDENT', '_DEDENT'):
                tokens.append(token)
            if token.type not in _IGNORED_TOKENS or token.type in parser.choices():
                parser.feed_token(token)
        tree = parser.feed_eof()

        return ModelBuilder(tokens, self._token_models, self._tree_models).build(tree, target)


class ModelBuilder:
    def __init__(self, tokens: list[lark.Token], token_models: dict[str, Type[models.RawTokenModel]], tree_models: dict[str, Type[models.RawTreeModel]]):
        self._tokens = tokens
        self._token_models = token_models 
        self._tree_models = tree_models
        self._built_tokens: list[models.RawTokenModel] = []
        self._token_to_index = {id(token): i for i, token in enumerate(tokens)}
        self._cursor = 0
        self._right_floating_placeholders: list[internal.Placeholder] = []
        self._token_store = models.TokenStore.from_tokens([])
        self._indents: list[list[models.RawTokenModel]] = [[]]
        self._is_line_start = True

    def _add_tokens(self, tokens: Iterable[models.RawTokenModel]) -> None:
        for token in tokens:
            self._built_tokens.append(token)
            if self._indents and self._is_line_start and isinstance(token, models.Whitespace):
                self._indents[-1].append(token)
            if isinstance(token, models.Newline):
                self._is_line_start = True
            elif token.raw_text:
                self._is_line_start = False

    def _fix_gap(self, cursor: int) -> None:
        for token in self._tokens[self._cursor:cursor]:
            if not token.value:  # skips EOL, _INDENT, _DEDENT, etc. if outside a model.
                continue
            self._add_tokens([self._token_models[token.type].from_raw_text(token.value)])
        self._cursor = cursor
        self._add_tokens(self._right_floating_placeholders)
        self._right_floating_placeholders.clear()

    def _build_placeholder(self, floating: _Floating) -> internal.Placeholder:
        placeholder = internal.Placeholder.from_default()
        if floating == _Floating.RIGHT:
            self._right_floating_placeholders.append(placeholder)
        elif floating == _Floating.LEFT:
            if self._right_floating_placeholders:
                raise ValueError('Floating direction cannot be satisified.')
            self._built_tokens.append(placeholder)
        else:
            assert False
        return placeholder

    def _build_token(self, token: lark.Token) -> models.RawTokenModel:
        self._fix_gap(self._token_to_index[id(token)])
        built_token = self._token_models[token.type].from_raw_text(token.value)
        self._add_tokens([built_token])
        self._cursor += 1
        return built_token

    def _build_tree(self, tree: lark.Tree) -> models.RawTreeModel:
        model_type = self._tree_models[tree.data]
        children = []
        for child in tree.children:
            is_tree = isinstance(child, lark.Tree)
            if is_tree and child.data == 'maybe_left':
                children.append(self._build_optional_node(child, _Floating.LEFT))
            elif is_tree and child.data == 'maybe_right':
                children.append(self._build_optional_node(child, _Floating.RIGHT))
            elif is_tree and child.data in ('repeated', 'repeated_sep'):
                children.append(self._build_repeated_node(child))
            else:
                children.append(self._build_required_node(child))
        indents: tuple[models.RawTokenModel, ...] = ()
        if hasattr(model_type, '_indent'):
            if not self._indents[-1]:
                raise exceptions.UnexpectedInput('Missing indent.')
            indents = (self._indents[-1][-1],)
        return model_type.from_parsed_children(self._token_store, *indents, *children)

    def _build_required_node(self, node: lark.Token | lark.Tree) -> models.RawModel:
        if isinstance(node, lark.Token):
            return self._build_token(node)
        if isinstance(node, lark.Tree):
            return self._build_tree(node)
        assert False

    def _build_optional_node(self, node: lark.Tree, floating: _Floating) -> models.RawModel:
        inner_node, = node.children
        if floating == _Floating.LEFT:
            placeholder = self._build_placeholder(floating)
            inner = self._build_required_node(inner_node) if inner_node is not None else None
            return internal.MaybeL(self._token_store, inner, placeholder)
        if floating == _Floating.RIGHT:
            inner = self._build_required_node(inner_node) if inner_node is not None else None
            placeholder = self._build_placeholder(floating)
            return internal.MaybeR(self._token_store, inner, placeholder)
        assert False

    def _build_repeated_node(self, node: lark.Tree) -> models.RawModel:
        placeholder = self._build_placeholder(_Floating.LEFT)
        indents: list[models.RawTokenModel] = []
        self._indents.append(indents)
        items = [
            self._build_required_node(child) for child in node.children
            if not (isinstance(child, lark.Tree) and child.data.endswith('_'))
        ]
        self._indents.pop()
        return internal.Repeated(self._token_store, items, placeholder, indents[0].raw_text if indents else '')

    def build(self, tree: lark.Tree, model_type: Type[_U]) -> _U:
        model = self._build_tree(tree)
        self._fix_gap(len(self._tokens))
        self._token_store.insert_after(None, self._built_tokens)
        assert isinstance(model, model_type)
        return model
