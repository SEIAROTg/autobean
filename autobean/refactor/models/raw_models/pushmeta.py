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
        self._key = key
        self._value = value

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        match self._value:
            case base.RawTokenModel():
                return self._value
            case base.RawTreeModel():
                return self._value.last_token
            case None:
                return self._key
            case _:
                assert False

    _label = internal.field[PushmetaLabel]()
    _key = internal.field[meta_key.MetaKey]()
    _value = internal.field[Optional[meta_value.MetaValue]]()

    raw_key = internal.required_node_property(_key)
    raw_value = internal.optional_node_property[meta_value.MetaValue](_value, floating=internal.Floating.LEFT)

    @raw_value.creator
    def __raw_value_creator(self, value: meta_value.MetaValue) -> None:
        self.token_store.insert_after(self._key, [
            punctuation.Whitespace(' '), *value.detach()])
        if isinstance(value, base.RawTreeModel):
            value.reattach(self.token_store)
    
    @raw_value.remover
    def __raw_value_remover(self, current: meta_value.MetaValue) -> None:
        editor.remove_towards_left(self, current)

    def clone(self: _SelfPushmeta, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> _SelfPushmeta:
        value: Optional[meta_value.MetaValue]
        if isinstance(self._value, base.RawTokenModel):
            value = token_transformer.transform(self._value)
        elif isinstance(self._value, base.RawTreeModel):
            value = self._value.clone(token_store, token_transformer)
        else:
            assert self._value is None
            value = self._value
        return type(self)(
            token_store,
            token_transformer.transform(self._label),
            token_transformer.transform(self._key),
            value)
    
    def _reattach(self, token_store: base.TokenStore, token_transformer: base.TokenTransformer) -> None:
        self._token_store = token_store
        self._label = token_transformer.transform(self._label)
        self._key = token_transformer.transform(self._key)
        if isinstance(self._value, base.RawTokenModel):
            self._value = token_transformer.transform(self._value)
        elif isinstance(self._value, base.RawTreeModel):
            self._value.reattach(token_store, token_transformer)
        else:
            assert self._value is None

    def _eq(self, other: base.RawTreeModel) -> bool:
        return (
            isinstance(other, Pushmeta) and
            self._key == other._key and
            self._value == other._value)

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
        self._key = key

    @property
    def first_token(self) -> base.RawTokenModel:
        return self._label

    @property
    def last_token(self) -> base.RawTokenModel:
        return self._key

    _label = internal.field[PopmetaLabel]()
    _key = internal.field[meta_key.MetaKey]()
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
