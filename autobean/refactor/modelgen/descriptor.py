import collections
import dataclasses
import enum
import functools
import inspect
import itertools
import pathlib
from typing import Any, ForwardRef, Iterable, Optional, Type, Union, get_args, get_origin
from lark import load_grammar
from lark import lexer
from lark import grammar
import stringcase  # type: ignore[import]
from autobean.refactor.meta_models import base

_Grammar = dict[str, lexer.TerminalDef | grammar.Rule | None]

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
    compiled: _Grammar = {
        **{terminal.name: terminal for terminal in terminals},
        **{rule.origin.name: rule for rule in rules},
    }
    for name, _ in g.term_defs:
        compiled.setdefault(name, None)  # those from %declare
    return compiled


_GRAMMAR = _load_grammar()


def _model_name_to_module(model_name: str) -> str:
    return {
        'Comma': 'punctuation',
        'Whitespace': 'punctuation',
        'Newline': 'punctuation',
        'Indent': 'punctuation',
        'Eol': 'punctuation',
        'MetaRawValue': 'meta_value',
        'MetaValue': 'meta_value',
        'UnitCost': 'cost',
        'TotalCost': 'cost',
    }.get(model_name) or stringcase.snakecase(model_name)


def _model_name_to_value_type(model_name: str) -> Optional[str]:
    return {
        # str
        'Account': 'str',
        'Currency': 'str',
        'EscapedString': 'str',
        'Link': 'str',
        'Tag': 'str',
        'MetaKey': 'str',
        'TransactionFlag': 'str',
        'PostingFlag': 'str',
        'Whitespace': 'str',
        'InlineComment': 'str',
        'BlockComment': 'str',
        # date
        'Date': 'datetime.date',
        # decimal
        'NumberExpr': 'decimal.Decimal',
        'Tolerance': 'decimal.Decimal',
        # bool
        'Bool': 'bool',
        # meta
        'MetaRawValue': 'MetaValue',
        # raw
        'Amount': 'Amount',
        'CostSpec': 'CostSpec',
        'PriceAnnotation': 'PriceAnnotation',
        'MetaItem': 'MetaItem',
        'Posting': 'Posting',
        'Directive': 'Directive',
    }.get(model_name)


def _rule_to_model_name(rule: str) -> str:
    return {
        'meta_value': 'MetaRawValue',
    }.get(rule) or stringcase.pascalcase(rule.lower())


def _fmt_separators(separators: tuple[str, ...]) -> str:
    if len(separators) == 1:
        inner = separators[0] + ','
    else:
        inner = ', '.join(separators)
    return '(' + inner + ')'


@enum.unique
class FieldCardinality(enum.Enum):
    REQUIRED = enum.auto()
    OPTIONAL = enum.auto()
    REPEATED = enum.auto()


@dataclasses.dataclass(frozen=True)
class ModelType:
    name: str
    rule: str

    @property
    def value_type(self) -> Optional[str]:
        return _model_name_to_value_type(self.name)


@dataclasses.dataclass(frozen=True)
class FieldDescriptor:
    name: str
    model_types: frozenset[ModelType]
    cardinality: FieldCardinality
    floating: Optional[base.Floating]
    is_public: bool
    define_as: Optional[str]
    type_alias: Optional[str]
    has_circular_dep: bool
    is_optional: bool
    is_keyword_only: bool
    default_value: Any
    separators: Optional[tuple[str, ...]]
    separators_before: Optional[tuple[str, ...]]
    default_indent: Optional[str] = None

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
    def value_types(self) -> Optional[list[str]]:
        if self.type_alias and (value_type := _model_name_to_value_type(self.type_alias)):
            return [value_type]
        values = []
        for model_type in self.model_types:
            if model_type.value_type is None:
                return None
            values.append(model_type.value_type)
        return values

    @functools.cached_property
    def value_type(self) -> Optional[str]:
        if self.value_types is None:
            return None
        return ' | '.join(sorted(self.value_types))

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
    def value_input_type(self) -> Optional[str]:
        if not self.value_types or len(self.value_types) != 1:
            return None
        value_type = self.value_type
        if value_type == 'MetaValue':
            value_type = 'MetaValue | MetaRawValue'
        elif value_type == 'MetaItem' and FieldCardinality.REPEATED:
            return 'Optional[Mapping[str, MetaValue | MetaRawValue]]'
        if self.cardinality == FieldCardinality.REQUIRED:
            return value_type
        elif self.cardinality == FieldCardinality.OPTIONAL:
            return f'Optional[{value_type}]'
        elif self.cardinality == FieldCardinality.REPEATED:
            return f'Iterable[{value_type}]'
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

    @functools.cached_property
    def define_default(self) -> Optional[str]:
        if not self.define_as:
            return None
        return get_literal_token_pattern(next(iter(self.model_types)).rule)

    @functools.cached_property
    def field_def(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return f'internal.required_field[{self.inner_type}]()'
        if self.cardinality == FieldCardinality.OPTIONAL:
            assert self.separators
            assert self.floating
            floating = {
                base.Floating.LEFT: 'left',
                base.Floating.RIGHT: 'right',
            }[self.floating]
            return f'internal.optional_{floating}_field[{self.inner_type}](separators={_fmt_separators(self.separators)})'
        if self.cardinality == FieldCardinality.REPEATED:
            assert self.separators
            args = [f'separators={_fmt_separators(self.separators)}']
            if self.separators_before is not None:
                args.append(f'separators_before={_fmt_separators(self.separators_before)}')
            if self.default_indent is not None:
                args.append(f'default_indent={self.default_indent!r}')
            return f'internal.repeated_field[{self.inner_type}]({", ".join(args)})'
        assert False

    @functools.cached_property
    def raw_property_def(self) -> str:
        if self.cardinality == FieldCardinality.REQUIRED:
            return f'internal.required_node_property(_{self.name})'
        if self.cardinality == FieldCardinality.OPTIONAL:
            return f'internal.optional_node_property(_{self.name})'
        if self.cardinality == FieldCardinality.REPEATED:
            if self.inner_type == 'MetaItem':
                return f'meta_item_internal.repeated_raw_meta_item_property(_{self.name})'
            return f'internal.repeated_node_property(_{self.name})'
        assert False

    @functools.cached_property
    def value_property_def(self) -> Optional[str]:
        if not self.is_public:
            return None
        if self.value_types is None or len(self.value_types) != 1:
            return None
        if self.value_type == self.inner_type and self.value_type != 'MetaItem':
            return f'raw_{self.name}'
        if self.cardinality == FieldCardinality.REQUIRED:
            if self.value_type == 'decimal.Decimal':
                return f'internal.required_decimal_property(raw_{self.name})'
            elif self.value_type == 'datetime.date':
                return f'internal.required_date_property(raw_{self.name})'
            elif self.value_type == 'str':
                return f'internal.required_string_property(raw_{self.name})'
        elif self.cardinality == FieldCardinality.OPTIONAL:
            if self.value_type == 'decimal.Decimal':
                return f'internal.optional_decimal_property(raw_{self.name}, {self.inner_type_original})'
            elif self.value_type == 'str':
                return f'internal.optional_string_property(raw_{self.name}, {self.inner_type_original})'
            elif self.value_type == 'MetaValue':
                return f'meta_value_internal.optional_meta_value_property(raw_{self.name})'
        elif self.cardinality == FieldCardinality.REPEATED:
            if self.value_type == 'str':
                return f'internal.repeated_string_property(raw_{self.name}, {self.inner_type_original})'
            elif self.value_type == 'MetaItem':
                return f'meta_item_internal.repeated_meta_item_property(_{self.name})'
        return None

    @functools.cached_property
    def from_children_default(self) -> str:
        if not self.is_optional or self.cardinality == FieldCardinality.REQUIRED:
            return ''
        if self.cardinality == FieldCardinality.OPTIONAL:
            return ' = None'
        if self.cardinality == FieldCardinality.REPEATED:
            return ' = ()'
        assert False

    @functools.cached_property
    def from_value_default(self) -> str:
        if not self.is_optional:
            return ''
        if self.value_type == 'MetaItem' and self.cardinality == FieldCardinality.REPEATED:
            return ' = None'
        if self.default_value:
            return f' = {self.default_value!r}'
        if self.cardinality == FieldCardinality.OPTIONAL:
            return ' = None'
        if self.cardinality == FieldCardinality.REPEATED:
            return ' = ()'
        assert False

    @functools.cached_property
    def construction_from_value(self) -> Optional[str]:
        if self.inner_type == 'MetaItem' and self.cardinality == FieldCardinality.REPEATED:
            return f'meta_item_internal.from_mapping({self.name}) if {self.name} is not None else ()'
        if self.value_type == self.inner_type:
            return self.name
        if not self.value_input_type:
            return None
        if self.inner_type == 'MetaRawValue':
            ctor = 'meta_value_internal.from_value'
        else:
            ctor = f'{self.inner_type}.from_value'
        if self.cardinality == FieldCardinality.REQUIRED:
            return f'{ctor}({self.name})'
        if self.cardinality == FieldCardinality.OPTIONAL:
            return f'{ctor}({self.name}) if {self.name} is not None else None'
        if self.cardinality == FieldCardinality.REPEATED:
            return f'map({ctor}, {self.name})'
        assert False


@dataclasses.dataclass
class MetaModelDescriptor:
    name: str
    rule: str
    fields: list[FieldDescriptor]

    @functools.cached_property
    def generate_from_value(self) -> bool:
        return all(
            field.value_input_type is not None and field.construction_from_value is not None
            for field in self.public_fields)

    @functools.cached_property
    def imports(self) -> dict[Optional[str], set[str]]:
        ret = collections.defaultdict[Optional[str], set[str]](set)
        ret['typing'].update(('TypeVar', 'Type', 'final'))
        if self.type_check_only_imports:
            ret['typing'].add('TYPE_CHECKING')
        ret['..'].update(('base', 'internal'))
        for field in self.fields:
            if field.cardinality == FieldCardinality.OPTIONAL:
                ret['typing'].add('Optional')
            elif field.cardinality == FieldCardinality.REPEATED:
                ret['typing'].add('Iterable')
            for sep in itertools.chain(field.separators or (), field.separators_before or ()):
                model_name = sep.split('.', 1)[0]
                module = _model_name_to_module(model_name)
                ret[f'..{module}'].add(model_name)
            for model_type in field.model_types:
                if self.generate_from_value and model_type.value_type:
                    *modules, _ = model_type.value_type.rsplit('.', 1)
                    if modules:
                        ret[None].add(modules[0])
                    if model_type.value_type == 'MetaValue':
                        ret['..meta_value'].add('MetaValue')
                        ret['..'].add('meta_value_internal')
                    elif model_type.value_type == 'MetaItem':
                        ret['..meta_value'].update(('MetaRawValue', 'MetaValue'))
                        ret['..'].add('meta_item_internal')
                        ret['typing'].update(('Optional', 'Mapping'))
                if model_type.value_type == 'MetaItem':
                    ret['..'].add('meta_item_internal')
            if not field.define_as and not field.has_circular_dep:
                for model_type in field.model_types:
                    module = _model_name_to_module(model_type.name)
                    ret[f'..{module}'].add(model_type.name)
        return ret

    @functools.cached_property
    def type_check_only_imports(self) -> dict[Optional[str], set[str]]:
        ret = collections.defaultdict[Optional[str], set[str]](set)
        for field in self.fields:
            if not field.define_as and field.has_circular_dep:
                for model_type in field.model_types:
                    module = _model_name_to_module(model_type.name)
                    ret[f'..{module}'].add(model_type.name)
        return ret

    @property
    def public_fields(self) -> Iterable[FieldDescriptor]:
        return (field for field in self.fields if field.is_public)

    @functools.cached_property
    def ctor_positional_fields(self) -> list[FieldDescriptor]:
        return [field for field in self.public_fields if not field.is_keyword_only]

    @functools.cached_property
    def ctor_keyword_fields(self) -> list[FieldDescriptor]:
        return [field for field in self.public_fields if field.is_keyword_only]


def is_token(rule: str) -> bool:
    return isinstance(_GRAMMAR[rule], lexer.TerminalDef)


def default_constructable(model_types: list[ModelType]) -> bool:
    if len(model_types) != 1:
        return False
    rule = next(iter(model_types)).rule
    r = _GRAMMAR[rule]
    return r is None or isinstance(r, lexer.TerminalDef) and r.pattern.type == 'str'


def get_literal_token_pattern(rule: str) -> Optional[str]:
    r = _GRAMMAR[rule]
    assert isinstance(r, lexer.TerminalDef)
    if r.pattern.type == 'str':
        return r.pattern.value
    return None


def build_descriptor(meta_model: Type[base.MetaModel]) -> MetaModelDescriptor:
    field_descriptors: list[FieldDescriptor] = []
    is_first = True
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
            raise ValueError('Fields with define_as must be a single token.')
        if not is_public and (not default_constructable(model_types) or cardinality != FieldCardinality.REQUIRED):
            raise ValueError('Private fields must be required and default constructable.')
        if field.default_value is not None and not field.is_optional:
            raise ValueError('Fields with default_value must set is_optional.')
        if field.is_optional and (cardinality == FieldCardinality.REQUIRED and field.default_value is None):
            raise ValueError('Required fields must not set is_optional or set default_value.')
        if field.is_keyword_only and not field.is_optional:
            raise ValueError('Fields with is_keyword_only must also set is_optional.')
        if field.separators_before is not None and cardinality != FieldCardinality.REPEATED:
            raise ValueError('Only repeated fields may specify separators_before.')
        separators = field.separators
        if field.separators is None:
            if is_first and cardinality == FieldCardinality.REQUIRED:
                separators = ()
            else:
                separators = ('Whitespace.from_default()',)
        descriptor = FieldDescriptor(
            name=name,
            model_types=frozenset(model_types),
            cardinality=cardinality,
            floating=floating,
            is_public=is_public,
            define_as=field.define_as,
            type_alias=field.type_alias,
            has_circular_dep=field.has_circular_dep,
            is_optional=field.is_optional,
            is_keyword_only=field.is_keyword_only,
            default_value=field.default_value,
            separators=separators,
            separators_before=field.separators_before,
            default_indent=field.default_indent,
        )
        field_descriptors.append(descriptor)
        is_first = False
    return MetaModelDescriptor(
        name=meta_model.__name__,
        rule=stringcase.snakecase(meta_model.__name__),
        fields=field_descriptors,
    )


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
        if not rule in _GRAMMAR:
            raise ValueError(f'Unknown rule: {rule}.')
        name = field.define_as or _rule_to_model_name(rule)
        model_types.append(ModelType(name=name, rule=rule))
    return model_types
