import dataclasses
import enum
import functools
import inspect
import pathlib
from typing import ForwardRef, Optional, Type, Union, get_args, get_origin
from lark import load_grammar
from lark import lexer
from lark import grammar
import stringcase  # type: ignore[import]
from autobean.refactor.meta_models import base

_Grammar = dict[str, lexer.TerminalDef | grammar.Rule]

_CURRENT_DIR = pathlib.Path(__file__).parent


def _load_grammar() -> _Grammar:
    with open(_CURRENT_DIR / '..' / 'beancount.lark') as f:
        g, _ = load_grammar.load_grammar(
            grammar=f.read(),
            source=f.name,
            import_paths=[],
            global_keep_all_tokens=False,
        )
    terminals: list[lexer.TerminalDef]
    rules: list[grammar.Rule]
    all_rules = {rule.value for rule, _, _, _ in g.rule_defs}
    terminals, rules, _ = g.compile(all_rules, '*')
    return {
        **{terminal.name: terminal for terminal in terminals},
        **{rule.origin.name: rule for rule in rules},
    }


_GRAMMAR = _load_grammar()


@enum.unique
class FieldCardinality(enum.Enum):
    REQUIRED = enum.auto()
    OPTIONAL = enum.auto()
    REPEATED = enum.auto()


@dataclasses.dataclass(frozen=True)
class FieldDescriptor:
    name: str
    rules: frozenset[str]
    cardinality: FieldCardinality
    floating: Optional[base.Floating]
    is_public: bool
    define_as: Optional[str]
    define_default: Optional[str]
    type_alias: Optional[str]

    def model_name(self, rule: str) -> str:
        return self.define_as or stringcase.pascalcase(rule.lower())

    @functools.cached_property
    def inner_type_original(self) -> str:
        model_names = []
        for rule in self.rules:
            model_name = self.model_name(rule)
            model_names.append(model_name)
        return ' | '.join(sorted(model_names))

    @functools.cached_property
    def inner_type(self) -> str:
        if self.type_alias is not None:
            return self.type_alias
        return self.inner_type_original

    @functools.cached_property
    def public_type(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return self.inner_type
        elif self.cardinality == FieldCardinality.OPTIONAL:
            return f'Optional[{self.inner_type}]'
        else:
            raise NotImplementedError()

    @functools.cached_property
    def private_type(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return self.inner_type
        elif self.cardinality == FieldCardinality.OPTIONAL:
            return f'internal.Maybe[{self.inner_type}]'
        else:
            raise NotImplementedError()

    @functools.cached_property
    def attribute_name(self) -> str:
        if self.is_public:
            return f'raw_{self.name}'
        else:
            return f'_{self.name}'


def is_literal_token(rule: str) -> bool:
    r = _GRAMMAR[rule]
    return isinstance(r, lexer.TerminalDef) and r.pattern.type == 'str'


def get_literal_token_pattern(rule: str) -> str:
    r = _GRAMMAR[rule]
    assert isinstance(r, lexer.TerminalDef) and r.pattern.type == 'str'
    return r.pattern.value


def extract_field_descriptors(meta_model: Type[base.MetaModel]) -> list[FieldDescriptor]:
    field_descriptors: list[FieldDescriptor] = []
    for name, type_hint in inspect.get_annotations(meta_model).items():
        field = getattr(meta_model, name, None) or base.field()
        is_public = not name.startswith('_')
        name = name.removeprefix('_')
        if isinstance(type_hint, str):
            rules = {type_hint}
            cardinality = FieldCardinality.REQUIRED
        elif get_origin(type_hint) is Union:
            rules = set[str]()
            cardinality = FieldCardinality.REQUIRED
            for arg in get_args(type_hint):
                if arg is type(None):
                    cardinality = FieldCardinality.OPTIONAL
                elif isinstance(arg, ForwardRef):
                    rules.add(arg.__forward_arg__)
                else:
                    raise ValueError(f'Unsupported type hint: {type_hint}')
        else:
            raise ValueError(f'Unsupported field type: {type_hint!r}.')
        for rule in rules:
            if not rule in _GRAMMAR:
                raise ValueError(f'Unknown rule: {rule}.')
        if cardinality == FieldCardinality.OPTIONAL and not field.floating:
            raise ValueError('Optional fields must declare floating direction.')
        default_constructable = len(rules) == 1 or is_literal_token(next(iter(rules)))
        if field.define_as and not default_constructable:
            raise ValueError(f'Fields with define_as must be default constructable.')
        if not is_public and (not default_constructable or cardinality != FieldCardinality.REQUIRED):
            raise ValueError(f'Private fields must be required and default constructable.')
        descriptor = FieldDescriptor(
            name=name,
            rules=frozenset(rules),
            cardinality=cardinality,
            floating=field.floating,
            is_public=is_public,
            define_as=field.define_as,
            define_default=get_literal_token_pattern(next(iter(rules))) if field.define_as else None,
            type_alias=field.type_alias,
        )
        field_descriptors.append(descriptor)
    return field_descriptors
