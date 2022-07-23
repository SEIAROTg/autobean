from typing import Optional, Type, TypeVar, final

from . import base
from . import editor
from . import meta_key
from . import meta_value
from . import internal
from . import punctuation

_SelfPushmeta = TypeVar('_SelfPushmeta', bound='Pushmeta')
_SelfPopmeta = TypeVar('_SelfPopmeta', bound='Popmeta')


@internal.token_model
class PushmetaLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'PUSHMETA'
    DEFAULT = 'pushmeta'


@internal.token_model
class PopmetaLabel(internal.SimpleDefaultRawTokenModel):
    RULE = 'POPMETA'
    DEFAULT = 'popmeta'


@internal.tree_model
class Pushmeta(base.RawTreeModel):
    RULE = 'pushmeta'

    @final
    def __init__(self, token_store: base.TokenStore, label: PushmetaLabel, key: meta_key.MetaKey, value: Optional[meta_value.MetaValue]):
        super().__init__(token_store)
        self._label = label
        self.raw_key = key
        self.raw_value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        match self.raw_value:
            case base.RawTokenModel():
                return self.raw_value
            case base.RawTreeModel():
                return self.raw_value.last_token
            case None:
                return self.raw_key
            case _:
                assert False

    @internal.required_node_property
    def raw_key(self) -> meta_key.MetaKey:
        pass

    @internal.optional_node_property[meta_value.MetaValue, 'Pushmeta']
    def raw_value(self) -> meta_value.MetaValue:
        pass

    @raw_value.creator
    def __raw_value_creator(self, value: meta_value.MetaValue) -> None:
        self.token_store.insert_after(self.raw_key, [
            punctuation.Whitespace(' '), *value.detach()])
        if isinstance(value, base.RawTreeModel):
            value.reattach(self.token_store)
    
    @raw_value.remover
    def __raw_value_remover(self, current: meta_value.MetaValue) -> None:
        editor.remove_towards_left(self, current)

    def clone(self: _SelfPushmeta, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfPushmeta:
        value: Optional[meta_value.MetaValue]
        if isinstance(self.raw_value, base.RawTokenModel):
            value = token_transformer.transform(self.raw_value)
        elif isinstance(self.raw_value, base.RawTreeModel):
            value = self.raw_value.clone(token_store, token_transformer)
        else:
            assert self.raw_value is None
            value = self.raw_value
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_key),
            value)
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        type(self).raw_key.reset(self, token_transformer.transform(self.raw_key))
        if isinstance(self.raw_value, base.RawTokenModel):
            type(self).raw_value.reset(self, token_transformer.transform(self.raw_value))
        elif isinstance(self.raw_value, base.RawTreeModel):
            self.raw_value.reattach(token_store, token_transformer)
        else:
            assert self.raw_value is None

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Pushmeta) and
            self.raw_key == other.raw_key and
            self.raw_value == other.raw_value)

    @classmethod
    def from_children(cls: Type[_SelfPushmeta], key: meta_key.MetaKey, value: Optional[meta_value.MetaValue] = None) -> _SelfPushmeta:
        label = PushmetaLabel.from_default()
        tokens = [
            label,
            punctuation.Whitespace(' '),
            *key.detach(),
        ]
        if value is not None:
            tokens.extend([
                punctuation.Whitespace(' '),
                *value.detach(),
            ])
        token_store = base.TokenStore.from_tokens(tokens)
        if isinstance(value, base.RawTreeModel):
            value.reattach(token_store)
        return cls(token_store, label, key, value)


@internal.tree_model
class Popmeta(base.RawTreeModel):
    RULE = 'popmeta'

    @final
    def __init__(self, token_store: base.TokenStore, label: PopmetaLabel, key: meta_key.MetaKey):
        super().__init__(token_store)
        self._label = label
        self.raw_key = key

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self.raw_key

    @internal.required_node_property
    def raw_key(self) -> meta_key.MetaKey:
        pass

    def clone(self: _SelfPopmeta, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfPopmeta:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self.raw_key))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        type(self).raw_key.reset(self, token_transformer.transform(self.raw_key))

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, Popmeta) and self.raw_key == other.raw_key

    @classmethod
    def from_children(cls: Type[_SelfPopmeta], key: meta_key.MetaKey) -> _SelfPopmeta:
        label = PopmetaLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            label,
            punctuation.Whitespace(' '),
            *key.detach(),
        ])
        return cls(token_store, label, key)
