import itertools
from typing import Callable, Iterable, Iterator, Optional, TypeVar
from .. import base
from ..spacing import Newline, Whitespace
from ..block_comment import BlockComment
from . import base_property, fields, properties, repeated

_M = TypeVar('_M', bound=base.RawModel)
_U = TypeVar('_U', bound=base.RawTreeModel)


def _get_boundary(
    start: base.RawTokenModel,
    succ: Callable[[base.RawTokenModel], Optional[base.RawTokenModel]],
    limit: base.RawTokenModel,
) -> base.RawTokenModel:
    prev, token = start, succ(start)
    while prev is not limit and token is not None and (
            isinstance(token, Newline | Whitespace | BlockComment) or not token.raw_text):
        prev, token = token, succ(token)
    return prev


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
        claimed_comments = []
        comment_set = (
            {id(comment) for comment in comments} if comments is not None else None)
        token_store = self._repeated.token_store
        start_boundary = _get_boundary(
            self._repeated.first_token, token_store.get_prev, self._model.first_token)
        # inclusive
        starts = itertools.chain(
            [start_boundary],
            map(lambda x: token_store.get_next(x.last_token), self._repeated.items))
        end_boundary = _get_boundary(
            self._repeated.last_token, token_store.get_next, self._model.last_token)
        # exclusive
        ends = itertools.chain(
            map(lambda x: x.first_token, self._repeated.items),
            [token_store.get_next(end_boundary)],
        )
        items: list[_M | BlockComment] = []
        for start, end, item in itertools.zip_longest(starts, ends, self._repeated.items):
            token = start
            while token is not None and token is not end:
                prev_token, token = token, self._repeated.token_store.get_next(token)
                if not isinstance(prev_token, BlockComment):
                    continue
                if comment_set is not None and id(prev_token) not in comment_set:
                    continue
                if prev_token.claimed:
                    continue
                if comment_set is not None:
                    comment_set.discard(id(prev_token))
                prev_token.claimed = True
                items.append(prev_token)
                claimed_comments.append(prev_token)
            if item is not None:
                items.append(item)
                if isinstance(item, BlockComment):
                    claimed_comments.append(item)
                    if comment_set is not None:
                        comment_set.discard(id(item))
        if comment_set:
            raise ValueError(f'{len(comment_set)} comment(s) not found.')
        self._repeated.items[:] = items
        return tuple(claimed_comments)

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
