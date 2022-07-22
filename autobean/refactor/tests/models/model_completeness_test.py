from typing import Iterable, Type
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models


def _model_map(models: Iterable[Type[raw_models.RawModel]]) -> dict[str, Type[raw_models.RawModel]]:
    return {model.RULE: model for model in models}


def test_token_model_completeness() -> None:
    raw_map = _model_map(raw_models.TOKEN_MODELS)
    easy_map = _model_map(easy_models.TOKEN_MODELS)
    assert set(raw_map.keys()) == set(easy_map.keys())
    for key in raw_map.keys():
        assert issubclass(easy_map[key], raw_map[key])


def test_tree_model_completeness() -> None:
    raw_map = _model_map(raw_models.TREE_MODELS)
    easy_map = _model_map(easy_models.TREE_MODELS)
    assert set(raw_map.keys()) == set(easy_map.keys())
    for key in raw_map.keys():
        assert issubclass(easy_map[key], raw_map[key])
