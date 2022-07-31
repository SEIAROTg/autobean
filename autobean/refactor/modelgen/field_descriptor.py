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
class ModelType:
    name: str
    rule: str
    module: Optional[str]


@dataclasses.dataclass(frozen=True)
class FieldDescriptor:
    name: str
    model_types: frozenset[ModelType]
    cardinality: FieldCardinality
    floating: Optional[base.Floating]
    is_public: bool
    define_as: Optional[str]
    define_default: Optional[str]
    type_alias: Optional[str]
    has_circular_dep: bool
    is_optional: bool

    @functools.cached_property
    def inner_type_original(self) -> str:
        t = ' | '.join(sorted(model_type.name for model_type in self.model_types))
        return f"'{t}'" if self.has_circular_dep else t

    @functools.cached_property
    def inner_type(self) -> str:
        if self.type_alias is not None:
            return self.type_alias
        return self.inner_type_original

    @functools.cached_property
    def input_type(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return self.inner_type
        elif self.cardinality == FieldCardinality.OPTIONAL:
            return f'Optional[{self.inner_type}]'
        elif self.cardinality == FieldCardinality.REPEATED:
            return f'Iterable[{self.inner_type}]'
        else:
            assert False

    @functools.cached_property
    def internal_type(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return self.inner_type
        elif self.cardinality == FieldCardinality.OPTIONAL:
            return f'internal.Maybe[{self.inner_type}]'
        elif self.cardinality == FieldCardinality.REPEATED:
            return f'internal.Repeated[{self.inner_type}]'
        else:
            assert False

    @functools.cached_property
    def attribute_name(self) -> str:
        if self.is_public:
            return f'raw_{self.name}'
        else:
            return f'_{self.name}'


def is_token(rule: str) -> bool:
    return isinstance(_GRAMMAR[rule], lexer.TerminalDef)


def is_literal_token(rule: str) -> bool:
    r = _GRAMMAR[rule]
    return isinstance(r, lexer.TerminalDef) and r.pattern.type == 'str'


def get_literal_token_pattern(rule: str) -> Optional[str]:
    r = _GRAMMAR[rule]
    assert isinstance(r, lexer.TerminalDef)
    if r.pattern.type == 'str':
        return r.pattern.value
    return None


def extract_field_descriptors(meta_model: Type[base.MetaModel]) -> list[FieldDescriptor]:
    field_descriptors: list[FieldDescriptor] = []
    for name, type_hint in inspect.get_annotations(meta_model).items():
        field = getattr(meta_model, name, None) or base.field()
        is_public = not name.startswith('_')
        name = name.removeprefix('_')
        rules, cardinality = _rules_and_cardinality_from_type(type_hint)
        model_types = _model_types_from_rules(rules, field)
        del rules
        if cardinality == FieldCardinality.OPTIONAL and not field.floating:
            raise ValueError('Optional fields must declare floating direction.')
        floating = field.floating
        if cardinality == FieldCardinality.REPEATED:
            floating = base.Floating.LEFT
        single_token = len(model_types) == 1 and is_token(next(iter(model_types)).rule)
        if field.define_as and not single_token:
            raise ValueError(f'Fields with define_as must be a single token.')
        default_constructable = len(model_types) == 1 and is_literal_token(next(iter(model_types)).rule)
        if not is_public and (not default_constructable or cardinality != FieldCardinality.REQUIRED):
            raise ValueError(f'Private fields must be required and default constructable.')
        if field.is_optional and cardinality == FieldCardinality.REQUIRED:
            raise ValueError(f'Required fields cannot be optional.')
        descriptor = FieldDescriptor(
            name=name,
            model_types=frozenset(model_types),
            cardinality=cardinality,
            floating=floating,
            is_public=is_public,
            define_as=field.define_as,
            define_default=(
                get_literal_token_pattern(next(iter(model_types)).rule)
                if field.define_as else None),
            type_alias=field.type_alias,
            has_circular_dep=field.has_circular_dep,
            is_optional=field.is_optional,
        )
        field_descriptors.append(descriptor)
    return field_descriptors


def _rules_and_cardinality_from_type(type_hint: Type) -> tuple[set[str], FieldCardinality]:
    is_repeated = get_origin(type_hint) is list
    if is_repeated:
        type_hint, = get_args(type_hint)
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
    if is_repeated:
        if cardinality == FieldCardinality.OPTIONAL:
            raise ValueError('Repeated item cannot be optional.')
        cardinality = FieldCardinality.REPEATED
    return rules, cardinality


def _model_types_from_rules(rules: set[str], field: base.field) -> list[ModelType]:
    model_types = []
    for rule in rules:
        *module, rule = rule.rsplit('.', maxsplit=1)
        if not rule in _GRAMMAR:
            raise ValueError(f'Unknown rule: {rule}.')
        model_types.append(ModelType(
            name=field.define_as or stringcase.pascalcase(rule.lower()),
            rule=rule,
            module=module[0] if module else stringcase.snakecase(rule.lower())))
    return model_types
