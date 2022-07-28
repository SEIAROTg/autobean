from typing import Iterable, Type
from autobean.refactor.models import easy_models
from autobean.refactor.models import raw_models


def test_token_model_completeness() -> None:
    assert raw_models.TOKEN_MODELS.keys() == easy_models.TOKEN_MODELS.keys()
    for key in raw_models.TOKEN_MODELS:
        assert issubclass(easy_models.TOKEN_MODELS[key], raw_models.TOKEN_MODELS[key])


def test_tree_model_completeness() -> None:
    assert raw_models.TREE_MODELS.keys() == easy_models.TREE_MODELS.keys()
    for key in raw_models.TREE_MODELS:
        assert issubclass(easy_models.TREE_MODELS[key], raw_models.TREE_MODELS[key])
