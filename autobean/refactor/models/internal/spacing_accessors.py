import re
from typing import Callable, Iterable, Optional, Sequence
from .. import base
from ..spacing import Newline, Whitespace

_SPACING_GROUP_RE = re.compile(r'([ \t]+)|(\r*\n)')


def _tokens_to_text(tokens: Iterable[base.RawTokenModel]) -> str:
    return ''.join(token.raw_text for token in tokens)


def _text_to_tokens(text: str) -> Iterable[base.RawTokenModel]:
    for whitespace, newline in _SPACING_GROUP_RE.findall(text):
        if whitespace:
            yield Whitespace.from_raw_text(whitespace)
        if newline:
            yield Newline.from_raw_text(newline)


def _find_spacing(
        token: Optional[base.RawTokenModel],
        succ: Callable[[base.RawTokenModel], Optional[base.RawTokenModel]],
) -> list[base.RawTokenModel]:
    tokens: list[base.RawTokenModel] = []
    while token is not None and not token.raw_text:
        token = succ(token)
    # must not interleave with special tokens to avoid removing them in spacing update.
    while isinstance(token, Newline | Whitespace):
        if token.raw_text:
            tokens.append(token)
        token = succ(token)
    return tokens


class SpacingAccessorsMixin(base.RawModel):

    @property
    def raw_spacing_before(self) -> tuple[base.RawTokenModel, ...]:
        if self.token_store is None:
            return ()
        return tuple(reversed(_find_spacing(
                self.token_store.get_prev(self.first_token),
                self.token_store.get_prev)))

    @raw_spacing_before.setter
    def raw_spacing_before(self, tokens: tuple[base.RawTokenModel, ...]) -> None:
        if self.token_store is None:
            raise ValueError('Cannot set spacing without a token store.')
        current_tokens = self.raw_spacing_before
        if current_tokens:
            self.token_store.splice(tokens, current_tokens[0], current_tokens[-1])
        else:
            self.token_store.insert_before(self.first_token, tokens)

    @property
    def spacing_before(self) -> str:
        return _tokens_to_text(self.raw_spacing_before)

    @spacing_before.setter
    def spacing_before(self, value: str) -> None:
        self.raw_spacing_before = tuple(_text_to_tokens(value))

    @property
    def raw_spacing_after(self) -> Sequence[base.RawTokenModel]:
        if self.token_store is None:
            return ()
        return tuple(_find_spacing(
                self.token_store.get_next(self.last_token),
                self.token_store.get_next))

    @raw_spacing_after.setter
    def raw_spacing_after(self, tokens: Sequence[base.RawTokenModel]) -> None:
        if self.token_store is None:
            raise ValueError('Cannot set spacing without a token store.')
        current_tokens = self.raw_spacing_after
        if current_tokens:
            self.token_store.splice(tokens, current_tokens[0], current_tokens[-1])
        else:
            self.token_store.insert_after(self.last_token, tokens)

    @property
    def spacing_after(self) -> str:
        return _tokens_to_text(self.raw_spacing_after)

    @spacing_after.setter
    def spacing_after(self, value: str) -> None:
        self.raw_spacing_after = tuple(_text_to_tokens(value))
