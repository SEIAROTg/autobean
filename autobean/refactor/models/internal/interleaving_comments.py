import itertools
from typing import Callable, Generic, Iterable, Iterator, MutableSet, Optional, TypeVar
from .. import base
from ..spacing import Newline, Whitespace
from ..block_comment import BlockComment
from . import base_property, fields, properties, repeated
from .placeholder import Placeholder

_M = TypeVar('_M', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)


class _Universe(MutableSet[int]):
    def __contains__(self, item: object) -> bool:
        return True

    def __iter__(self) -> Iterator[int]:
        raise NotImplementedError()

    def __len__(self) -> int:
        return 0

    def add(self, item: int) -> None:
        pass

    def discard(self, item: int) -> None:
        pass


def _shift_ignored(
        token_store: base.TokenStore,
        first: base.RawTokenModel,
        last: base.RawTokenModel,
        *,
        backwards: bool,
) -> None:
    ignored: list[base.RawTokenModel] = []
    others: list[base.RawTokenModel] = []
    for token in token_store.iter(first, last):
        if isinstance(token, Placeholder):
            ignored.append(token)
        else:
            others.append(token)
    if not ignored:
        return None
    if backwards:
        token_store.splice(ignored + others ,first, last)
    else:
        token_store.splice(others + ignored, first, last)


class _CommentClaimer(Generic[_M]):
    def __init__(
            self,
            repeated: repeated.Repeated[_M | BlockComment],
            model: base.RawTreeModel,
            comments: Optional[Iterable[BlockComment]]):
        self._repeated = repeated
        self._model = model
        self._comments_to_claim = (
            {id(comment) for comment in comments} if comments is not None else _Universe())

    def _find_inner(self) -> Iterator[_M | BlockComment]:
        token_store = self._repeated.token_store
        # inclusive
        starts = itertools.chain(
            [self._repeated.first_token],
            map(lambda x: token_store.get_next(x.last_token), self._repeated.items))
        # exclusive
        ends = map(lambda x: x.first_token, self._repeated.items)
        for start, end, item in zip(starts, ends, self._repeated.items):
            token = start
            while token is not None and token is not end:
                prev_token, token = token, self._repeated.token_store.get_next(token)
                if not isinstance(prev_token, BlockComment):
                    continue
                if id(prev_token) not in self._comments_to_claim:
                    continue
                if prev_token.claimed:
                    continue
                self._comments_to_claim.discard(id(prev_token))
                yield prev_token
            yield item
            self._comments_to_claim.discard(id(item))
    
    def _find_outer(
            self,
            start: base.RawTokenModel,
            succ: Callable[[base.RawTokenModel], Optional[base.RawTokenModel]],
            *,
            limit: base.RawTokenModel,
    ) -> Iterator[BlockComment]:
        prev, token = start, succ(start)
        while prev is not limit and token is not None:
            if isinstance(token, Newline | Whitespace) or not token.raw_text:
                pass
            elif isinstance(token, BlockComment):
                if token.claimed:
                    break
                if id(token) in self._comments_to_claim:
                    yield token
            else:
                break
            prev, token = token, succ(token)

    def claim(self) -> list[BlockComment]:
        comments_before = list(self._find_outer(
            self._repeated.first_token,
            self._repeated.token_store.get_prev,
            limit=self._model.first_token))
        comments_before.reverse()
        items_inner = list(self._find_inner())
        comments_after = list(self._find_outer(
            self._repeated.last_token,
            self._repeated.token_store.get_next,
            limit=self._model.last_token))

        if self._comments_to_claim:
            raise ValueError(f'{len(self._comments_to_claim)} comment(s) not found.')

        if comments_before:
            first = self._repeated.token_store.get_prev(self._repeated.first_token)
            assert first is not None
            _shift_ignored(
                self._repeated.token_store, first, comments_before[0], backwards=True)

        if comments_after:
            first = self._repeated.token_store.get_next(self._repeated.last_token)
            assert first is not None
            _shift_ignored(
                self._repeated.token_store, first, comments_after[-1], backwards=False)

        items = list(itertools.chain(comments_before, items_inner, comments_after))
        comments = []
        for item in items:
            if isinstance(item, BlockComment):
                comments.append(item)
                item.claimed = True
        self._repeated.items[:] = items
        return comments


class RepeatedNodeWithInterleavingCommentsWrapper(properties.RepeatedNodeWrapper[_M | BlockComment]):

    def __init__(
            self,
            repeated: repeated.Repeated[_M | BlockComment],
            field: fields.repeated_field,
            model: base.RawTreeModel,
    ) -> None:
        super().__init__(repeated, field)
        self._model = model

    def claim_interleaving_comments(
            self,
            comments: Optional[Iterable[BlockComment]] = None,
    ) -> tuple[BlockComment, ...]:
        return tuple(_CommentClaimer(self._repeated, self._model, comments).claim())

    def unclaim_interleaving_comments(
            self,
            comments: Optional[Iterable[BlockComment]] = None,
    ) -> tuple[BlockComment, ...]:
        unclaimed_comments = []
        comment_set = (
            {id(comment) for comment in comments} if comments is not None else None)
        items: list[_M | BlockComment] = []
        for item in self._repeated.items:
            if not isinstance(item, BlockComment):
                items.append(item)
                continue
            if comment_set is not None and id(item) not in comment_set:
                items.append(item)
                continue
            if comment_set is not None:
                comment_set.discard(id(item))
            item.claimed = False
            unclaimed_comments.append(item)
        if comment_set:
            raise ValueError(f'{len(comment_set)} comment(s) not found.')
        self._repeated.items[:] = items
        return tuple(unclaimed_comments)

    def auto_claim_comments(self) -> None:
        super().auto_claim_comments()
        self.claim_interleaving_comments()


class repeated_node_with_interleaving_comments_property(
        base_property.base_ro_property[RepeatedNodeWithInterleavingCommentsWrapper[_M], base.RawTreeModel]):
    def __init__(self, inner_field: fields.repeated_field[_M | BlockComment]) -> None:
        super().__init__()
        self._inner_field = inner_field

    def __set_name__(self, owner: base.RawTreeModel, name: str) -> None:
        self._attr = name

    def _get(self, instance: _U) -> RepeatedNodeWithInterleavingCommentsWrapper[_M]:
        wrapper = instance.__dict__.get(self._attr)
        if wrapper is None:
            repeated = self._inner_field.__get__(instance)
            wrapper = RepeatedNodeWithInterleavingCommentsWrapper(repeated, self._inner_field, instance)
            instance.__dict__[self._attr] = wrapper
        return wrapper

    def __set__(self, instance: _U, value: RepeatedNodeWithInterleavingCommentsWrapper[_M]) -> None:
        repeated = self._inner_field.__get__(instance)
        properties.replace_node(repeated, value.repeated)
        self._inner_field.__set__(instance, value.repeated)
        instance.__dict__[self._attr] = value
