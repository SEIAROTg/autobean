import inspect
import pathlib
import sys
from typing import Type
import mako.template  # type: ignore[import]
import stringcase  # type: ignore[import]
from autobean.refactor.meta_models.base import MetaModel
from autobean.refactor.meta_models import meta_models
from autobean.refactor.modelgen import field_descriptor


_CURRENT_DIR = pathlib.Path(__file__).parent
with open(_CURRENT_DIR / 'raw_model.mako') as f:
    _RAW_MODEL_TMPL = mako.template.Template(f.read())


def collect_meta_models() -> list[Type[MetaModel]]:
    rets = []
    for _, meta_model in inspect.getmembers(meta_models, inspect.isclass):
        if issubclass(meta_model, MetaModel) and meta_model is not MetaModel:
            rets.append(meta_model)
    return rets


def generate_raw_models(meta_model: Type[MetaModel]) -> str:
    return _RAW_MODEL_TMPL.render(
        model_name=meta_model.__name__,
        fields=field_descriptor.extract_field_descriptors(meta_model),
    )


def raw_model_path(meta_model: Type[MetaModel]) -> str:
    filename = f'{stringcase.snakecase(meta_model.__name__)}.py'
    return str(_CURRENT_DIR / '..' / 'models' / 'raw_models' / 'generated' / filename)


if __name__ == '__main__':
    _, target = sys.argv
    all_meta_models = collect_meta_models()
    generated = 0
    for meta_model in all_meta_models:
        if target == 'all' or target == meta_model.__name__:
            with open(raw_model_path(meta_model), 'w') as f:
                f.write(generate_raw_models(meta_model))
            print(f'Generated {meta_model.__name__}.')
            generated += 1
    print(f'Generated {generated} models.')
