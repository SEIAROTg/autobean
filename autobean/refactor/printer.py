import io
from typing import TypeVar
from autobean.refactor.models import raw_models

_T = TypeVar('_T', bound=io.TextIOBase)


def print_model(model: raw_models.RawModel, file: _T) -> _T:
    for token in model.tokens:
        file.write(token.raw_text)
    return file
