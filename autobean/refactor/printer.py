import io
from typing import TypeVar
from autobean.refactor.models import raw_models


_T = TypeVar('_T', bound=io.TextIOBase)

def print_model(model: raw_models.RawModel, file: _T) -> _T:
    current = model.first_token
    last = model.last_token
    while current:
        file.write(current.raw_text)
        if current is last:
            break
        current = current.get_next()
    return file
