from typing import Optional, Type, TypeVar, final

from . import base
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
    def __init__(self, token_store: base.TokenStore, label: PushmetaLabel, key: meta_key.MetaKey, value: internal.Maybe[meta_value.MetaValue]):
        super().__init__(token_store)
        self._label = label
        self._key = key
        self._value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._value.last_token

    _label = internal.required_field[PushmetaLabel]()
    _key = internal.required_field[meta_key.MetaKey]()
    _value = internal.optional_field[meta_value.MetaValue](floating=internal.Floating.LEFT, separators=(punctuation.Whitespace.from_default(),))

    raw_key = internal.required_node_property(_key)
    raw_value = internal.optional_node_property[meta_value.MetaValue](_value)

    def clone(self: _SelfPushmeta, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfPushmeta:
        return type(self)(
            token_store,
            self._label.clone(token_store, token_transformer),
            self._key.clone(token_store, token_transformer),
            self._value.clone(token_store, token_transformer))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = self._label.reattach(token_store, token_transformer)
        self._key = self._key.reattach(token_store, token_transformer)
        self._value = self._value.reattach(token_store, token_transformer)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Pushmeta) and
            self._key == other._key and
            self._value == other._value)

    @classmethod
    def from_children(cls: Type[_SelfPushmeta], key: meta_key.MetaKey, value: Optional[meta_value.MetaValue] = None) -> _SelfPushmeta:
        label = PushmetaLabel.from_default()
        maybe_value = internal.MaybeL[meta_value.MetaValue].from_children(value, separators=cls._value.separators)
        tokens = [
            label,
            punctuation.Whitespace(' '),
            *key.detach(),
            *maybe_value.detach(),
        ]
        token_store = base.TokenStore.from_tokens(tokens)
        if isinstance(value, base.RawTreeModel):
            value.reattach(token_store)
        return cls(token_store, label, key, maybe_value)


@internal.tree_model
class Popmeta(base.RawTreeModel):
    RULE = 'popmeta'

    @final
    def __init__(self, token_store: base.TokenStore, label: PopmetaLabel, key: meta_key.MetaKey):
        super().__init__(token_store)
        self._label = label
        self._key = key

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._key

    _label = internal.required_field[PopmetaLabel]()
    _key = internal.required_field[meta_key.MetaKey]()
    raw_key = internal.required_node_property(_key)

    def clone(self: _SelfPopmeta, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfPopmeta:
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self._key))
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        self._key = token_transformer.transform(self._key)

    def _eq(self, other: base.RawTreeModel) -> bool:
        return isinstance(other, Popmeta) and self._key == other._key

    @classmethod
    def from_children(cls: Type[_SelfPopmeta], key: meta_key.MetaKey) -> _SelfPopmeta:
        label = PopmetaLabel.from_default()
        token_store = base.TokenStore.from_tokens([
            label,
            punctuation.Whitespace(' '),
            *key.detach(),
        ])
        return cls(token_store, label, key)
