# pylance: disable
# type: ignore

from typing import Optional, Union
from .base import MetaModel, Floating, field


# Auxiliary


class NumberUnaryExpr(MetaModel):
    unary_op: 'UNARY_OP' = field(define_as='UnaryOp')
    operand: 'number_atom_expr' = field(has_circular_dep=True)


class NumberParenExpr(MetaModel):
    _left_paren: 'LEFT_PAREN' = field(define_as='LeftParen')
    inner_expr: 'number_add_expr' = field(has_circular_dep=True)
    _right_paren: 'RIGHT_PAREN' = field(define_as='RightParen')


class NumberExpr(MetaModel):
    number_add_expr: 'number_add_expr' = field(has_circular_dep=True)


class Amount(MetaModel):
    number: 'number_expr'
    currency: 'CURRENCY'


class Tolerance(MetaModel):
    _tilde: 'TILDE' = field(define_as='Tilde')
    number: 'number_expr'


class UnitPrice(MetaModel):
    _label: 'AT' = field(define_as='At')
    number: Optional['number_expr'] = field(floating=Floating.LEFT)
    currency: Optional['CURRENCY'] = field(floating=Floating.LEFT)


class TotalPrice(MetaModel):
    _label: 'ATAT' = field(define_as='AtAt')
    number: Optional['number_expr'] = field(floating=Floating.LEFT)
    currency: Optional['CURRENCY'] = field(floating=Floating.LEFT)


class CompoundAmount(MetaModel):
    number_per: Optional['number_expr'] = field(floating=Floating.RIGHT)
    _hash: 'HASH' = field(define_as='Hash')
    number_total: Optional['number_expr'] = field(floating=Floating.LEFT)
    currency: 'CURRENCY'


class UnitCost(MetaModel):
    _left_brace: 'LEFT_BRACE' = field(define_as='LeftBrace')
    components: list['cost_component'] = field(
        separators=('Comma.from_default()', 'Whitespace.from_default()'),
        separators_before=())
    _right_brace: 'RIGHT_BRACE' = field(define_as='RightBrace', separators=())


class TotalCost(MetaModel):
    _dbl_left_brace: 'DBL_LEFT_BRACE' = field(define_as='DblLeftBrace')
    components: list['cost_component'] = field(
        separators=('Comma.from_default()', 'Whitespace.from_default()'),
        separators_before=())
    _dbl_right_brace: 'DBL_RIGHT_BRACE' = field(define_as='DblRightBrace', separators=())


class CostSpec(MetaModel):
    cost: Union['cost.unit_cost', 'cost.total_cost']


class Posting(MetaModel):
    indent: 'punctuation.INDENT'
    flag: Optional['POSTING_FLAG'] = field(floating=Floating.RIGHT)
    account: 'ACCOUNT' = field(separators=())
    number: Optional['number_expr'] = field(floating=Floating.LEFT)
    currency: Optional['CURRENCY'] = field(floating=Floating.LEFT)
    cost: Optional['cost_spec'] = field(floating=Floating.LEFT)
    price: Optional[Union['unit_price', 'total_price']] = field(
        floating=Floating.LEFT, type_alias='PriceAnnotation')


# Directives


class Include(MetaModel):
    _label: 'INCLUDE' = field(define_as='IncludeLabel')
    filename: 'ESCAPED_STRING'


class Option(MetaModel):
    _label: 'OPTION' = field(define_as='OptionLabel')
    key: 'ESCAPED_STRING'
    value: 'ESCAPED_STRING'


class Plugin(MetaModel):
    _label: 'PLUGIN' = field(define_as='PluginLabel')
    name: 'ESCAPED_STRING'
    config: Optional['ESCAPED_STRING'] = field(floating=Floating.LEFT, is_optional=True)


class Popmeta(MetaModel):
    _label: 'POPMETA' = field(define_as='PopmetaLabel')
    key: 'META_KEY'


class Poptag(MetaModel):
    _label: 'POPTAG' = field(define_as='PoptagLabel')
    tag: 'TAG'


class Pushmeta(MetaModel):
    _label: 'PUSHMETA' = field(define_as='PushmetaLabel')
    key: 'META_KEY'
    value: Optional['meta_value'] = field(floating=Floating.LEFT, type_alias='meta_value.MetaRawValue')


class Pushtag(MetaModel):
    _label: 'PUSHTAG' = field(define_as='PushtagLabel')
    tag: 'TAG'


# Entries


class Balance(MetaModel):
    date: 'DATE'
    _label: 'BALANCE' = field(define_as='BalanceLabel')
    account: 'ACCOUNT'
    number: 'number_expr'
    tolerance: Optional['tolerance'] = field(floating=Floating.LEFT)
    currency: 'CURRENCY'


class Close(MetaModel):
    date: 'DATE'
    _label: 'CLOSE' = field(define_as='CloseLabel')
    account: 'ACCOUNT'


class Commodity(MetaModel):
    date: 'DATE'
    _label: 'COMMODITY' = field(define_as='CommodityLabel')
    currency: 'CURRENCY'


class Event(MetaModel):
    date: 'DATE'
    _label: 'EVENT' = field(define_as='EventLabel')
    type: 'ESCAPED_STRING'
    description: 'ESCAPED_STRING'


class Pad(MetaModel):
    date: 'DATE'
    _label: 'PAD' = field(define_as='PadLabel')
    account: 'ACCOUNT'
    source_account: 'ACCOUNT'


class Price(MetaModel):
    date: 'DATE'
    _label: 'PRICE' = field(define_as='PriceLabel')
    currency: 'CURRENCY'
    amount: 'amount'


class Query(MetaModel):
    date: 'DATE'
    _label: 'QUERY' = field(define_as='QueryLabel')
    name: 'ESCAPED_STRING'
    query_string: 'ESCAPED_STRING'


class Note(MetaModel):
    date: 'DATE'
    _label: 'NOTE' = field(define_as='NoteLabel')
    account: 'ACCOUNT'
    comment: 'ESCAPED_STRING'


class Document(MetaModel):
    date: 'DATE'
    _label: 'DOCUMENT' = field(define_as='DocumentLabel')
    account: 'ACCOUNT'
    filename: 'ESCAPED_STRING'
    tags_links: list[Union['TAG', 'LINK']] = field(is_optional=True)


class Open(MetaModel):
    date: 'DATE'
    _label: 'OPEN' = field(define_as='OpenLabel')
    account: 'ACCOUNT'
    currencies: list['CURRENCY'] = field(
        separators=('Comma.from_default()', 'Whitespace.from_default()'),
        separators_before=('Whitespace.from_default()',),
        is_optional=True)
    booking: Optional['ESCAPED_STRING'] = field(floating=Floating.LEFT, is_optional=True)


class Custom(MetaModel):
    date: 'DATE'
    _label: 'CUSTOM' = field(define_as='CustomLabel')
    type: 'ESCAPED_STRING'
    values: list[Union[
        'ESCAPED_STRING',
        'DATE',
        'BOOL',
        'amount',
        'number_expr',
        'ACCOUNT',
    ]] = field(type_alias='CustomRawValue')
