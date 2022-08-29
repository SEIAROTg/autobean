<%
from autobean.refactor.modelgen.descriptor import FieldCardinality
from autobean.refactor.meta_models.base import Floating


def import_sort_key(item: tuple[str, set[str]]) -> tuple[bool, str]:
    return (item[0].startswith('.'), item)
%>\
# DO NOT EDIT
# This file is automatically generated by autobean.refactor.modelgen.

% for module in sorted(model.imports.pop(None, ())):
import ${module}
% endfor
% for module, imports in sorted(model.imports.items(), key=import_sort_key):
from ${module} import ${', '.join(sorted(imports))}
% endfor
% if model.type_check_only_imports:
if TYPE_CHECKING:
% for module in sorted(model.type_check_only_imports.pop(None, ())):
import ${module}
% endfor
% for module, imports in sorted(model.type_check_only_imports.items(), key=import_sort_key):
  from ${module} import ${', '.join(sorted(imports))}
% endfor
% endif

% for field in model.fields:
% if field.type_alias is not None and field.type_alias != field.inner_type_original:
${field.type_alias} = ${field.inner_type_original}
% endif
% endfor
_Self = TypeVar('_Self', bound='${model.name}')
% for field in model.fields:
% if field.define_as:


@internal.token_model
% if field.define_default is not None:
class ${field.define_as}(internal.SimpleDefaultRawTokenModel):
    RULE = '${next(iter(field.model_types)).rule}'
    DEFAULT = '${field.define_default}'
% else:
class ${field.define_as}(internal.SimpleRawTokenModel):
    RULE = '${next(iter(field.model_types)).rule}'
% endif
% endif
% endfor


@internal.tree_model
class ${model.name}(base.RawTreeModel):
    RULE = '${model.rule}'

% for field in model.fields:
    _${field.name} = ${field.field_def}
% endfor

% for field in model.public_fields:
    raw_${field.name} = ${field.raw_property_def}
% endfor

<% any_value_property = False %>\
% for field in model.fields:
% if field.value_property_def is not None:
    ${field.name} = ${field.value_property_def}
<% any_value_property = True %>\
% endif
% endfor
% if any_value_property:

% endif
    @final
    def __init__(
            self,
            token_store: base.TokenStore,
% for field in model.fields:
            ${field.name}: ${field.internal_type},
% endfor
    ):
        super().__init__(token_store)
% for field in model.fields:
        self._${field.name} = ${field.name}
% endfor

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._${model.fields[0].name}.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._${model.fields[-1].name}.last_token

    def clone(self: _Self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _Self:
        return type(self)(
            token_store,
% for field in model.fields:
            self._${field.name}.clone(token_store, token_transformer),
% endfor
        )

    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
% for field in model.fields:
        self._${field.name} = self._${field.name}.reattach(token_store, token_transformer)
% endfor

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, ${model.name})
% for field in model.fields:
            and self._${field.name} == other._${field.name}
% endfor
        )

    @classmethod
    def from_children(
            cls: Type[_Self],
% for field in model.public_fields:
            ${field.name}: ${field.input_type}${field.from_children_default},
% endfor
    ) -> _Self:
% for field in model.fields:
% if not field.is_public:
        ${field.name} = ${field.inner_type}.from_default()
% elif field.cardinality == FieldCardinality.OPTIONAL:
        maybe_${field.name} = cls._${field.name}.create_maybe(${field.name})
% elif field.cardinality == FieldCardinality.REPEATED:
        repeated_${field.name} = cls._${field.name}.create_repeated(${field.name})
% endif
% endfor
<%
skip_space = True
args = []
%>\
        tokens = [
% for field in model.fields:
% if not skip_space and field.cardinality == FieldCardinality.REQUIRED:
% for sep in field.separators:
            ${sep},
% endfor
% endif
<% skip_space = False %>\
% if field.cardinality == FieldCardinality.REQUIRED:
            *${field.name}.detach(),
<%
args.append(field.name)
%>\
% elif field.cardinality == FieldCardinality.OPTIONAL:
            *maybe_${field.name}.detach(),
<%
skip_space = field.floating == Floating.RIGHT
args.append(f'maybe_{field.name}')
%>\
% elif field.cardinality == FieldCardinality.REPEATED:
            *repeated_${field.name}.detach(),
<%
args.append(f'repeated_{field.name}')
%>\
% else:
<% assert False %>\
% endif
% endfor
        ]
        token_store = base.TokenStore.from_tokens(tokens)
% for arg in args:
        ${arg}.reattach(token_store)
% endfor
        return cls(token_store, ${', '.join(args)})
% if model.generate_from_value:

    @classmethod
    def from_value(
            cls: Type[_Self],
% for field in model.from_value_positional_fields:
            ${field.name}: ${field.value_input_type}${field.from_value_default},
% endfor
% if model.from_value_keyword_fields:
            *,
% for field in model.from_value_keyword_fields:
            ${field.name}: ${field.value_input_type}${field.from_value_default},
% endfor
% endif
    ) -> _Self:
        return cls.from_children(
% for field in model.public_fields:
            ${field.construction_from_value},
% endfor
        )
% endif
