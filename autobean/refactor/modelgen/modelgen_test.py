import collections
import os
from typing import Type
import pytest
from autobean.refactor.meta_models import base
from . import generate


@pytest.mark.parametrize(
    'meta_model', generate.collect_meta_models(),
)
def test_raw_model_in_sync(meta_model: Type[base.MetaModel]) -> None:
    expected = generate.generate_raw_models(meta_model)
    if not os.path.exists(generate.raw_model_path(meta_model)):
        pytest.fail(f'Meta model {meta_model.__name__} is not generated.')
    with open(generate.raw_model_path(meta_model)) as f:
        actual = f.read()
    assert actual == expected, f'{meta_model.__name__} is out of sync.'


def test_raw_model_extra_files() -> None:
    files_by_dir = collections.defaultdict(set)
    for meta_model in generate.collect_meta_models():
        dirname, filename = os.path.split(generate.raw_model_path(meta_model))
        files_by_dir[dirname].add(filename)
    for dirname, filenames in files_by_dir.items():
        actual_filenames = set(os.listdir(dirname))
        extra_files = actual_filenames - filenames - {'__init__.py', '__pycache__'}
        assert not extra_files, f'Found extra files {extra_files}.'
 