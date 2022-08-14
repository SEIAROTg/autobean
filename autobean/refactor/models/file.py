from . import base
from . import internal
from .generated import file
from .generated.file import Directive


@internal.tree_model
class File(file.File):

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._token_store.get_first() or self._directives.first_token

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._token_store.get_last() or self._directives.last_token
