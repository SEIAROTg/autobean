import datetime
import io
import re
import textwrap
from typing import Any
from beancount.parser import printer
from beancount.core.data import Directive, Transaction
from beancount.ops import balance
from beancount.parser import booking, parser
import pytest
from .plugin import Plugin


_FOO_TEXT = textwrap.dedent('''
    2000-01-01 open Assets:Foo
    2000-01-01 open Assets:Bar
    2000-01-01 open Income:Foo
    2000-02-01 *
        Income:Foo   -500.00 USD
        Assets:Foo   100.00 STOCK {{500 USD}}

    2000-03-01 *
        Income:Foo
        Assets:Foo   100.00 STOCK {6 USD}

    2000-04-01 *
        Income:Foo
        Assets:Bar   100.00 STOCK {6 USD}
    
    2000-05-01 balance Assets:Foo 200.00 STOCK
    2000-05-01 balance Assets:Bar 100.00 STOCK
    
    2000-05-01 custom "autobean.stock_split" 10 STOCK

    2000-05-02 balance Assets:Foo 2000.00 STOCK
    2000-05-02 balance Assets:Bar 1000.00 STOCK

    2000-05-03 *
        Income:Foo   -1 USD
        Assets:Bar   1 STOCK.B {{1 USD}}

    2000-05-04 balance Assets:Foo 2000.00 STOCK
    2000-05-04 balance Assets:Bar 1000.00 STOCK
    2000-05-04 balance Assets:Bar 1 STOCK.B

    2000-05-05 custom "autobean.stock_split" 2 STOCK

    2000-05-06 balance Assets:Foo 4000.00 STOCK
    2000-05-06 balance Assets:Bar 2000.00 STOCK
    2000-05-06 balance Assets:Bar 1 STOCK.B

    2000-05-07 custom "autobean.stock_split" 2 STOCK.B

    2000-05-08 balance Assets:Foo 4000.00 STOCK
    2000-05-08 balance Assets:Bar 2000.00 STOCK
    2000-05-08 balance Assets:Bar 2 STOCK.B
''')


def load(text: str) -> tuple[list[Directive], list[Any]]:
    entries, parsing_errors, options_map = parser.parse_string(text)
    entries, booking_errors = booking.book(entries, options_map)
    entries, plugin_errors = Plugin.plugin(entries, options_map)
    entries, balance_errors = balance.check(entries, options_map)
    return entries, [
        *parsing_errors,
        *booking_errors,
        *plugin_errors,
        *balance_errors,
    ]


def test_ok() -> None:
    entries, errors = load(_FOO_TEXT)
    assert not errors
    txn = entries[-15]
    assert isinstance(txn, Transaction)
    assert txn.date == datetime.date(2000, 5, 1)
    assert txn.narration == 'STOCK split 10:1'
    f = io.StringIO()
    printer.print_entry(txn, file=f)
    text = '\n'.join(sorted(filter(None, re.sub(r' +', ' ', f.getvalue()).split('\n')[1:])))
    assert text == '''\
 Assets:Bar -100.00 STOCK {6 USD, 2000-04-01}
 Assets:Bar 1000.00 STOCK {0.6 USD, 2000-04-01}
 Assets:Foo -100.00 STOCK {5 USD, 2000-02-01}
 Assets:Foo -100.00 STOCK {6 USD, 2000-03-01}
 Assets:Foo 1000.00 STOCK {0.5 USD, 2000-02-01}
 Assets:Foo 1000.00 STOCK {0.6 USD, 2000-03-01}\
'''

    txn = entries[-8]
    assert isinstance(txn, Transaction)
    assert txn.date == datetime.date(2000, 5, 5)
    assert txn.narration == 'STOCK split 2:1'
    f = io.StringIO()
    printer.print_entry(txn, file=f)
    text = '\n'.join(sorted(filter(None, re.sub(r' +', ' ', f.getvalue()).split('\n')[1:])))
    assert text == '''\
 Assets:Bar -1000.00 STOCK {0.6 USD, 2000-04-01}
 Assets:Bar 2000.00 STOCK {0.3 USD, 2000-04-01}
 Assets:Foo -1000.00 STOCK {0.5 USD, 2000-02-01}
 Assets:Foo -1000.00 STOCK {0.6 USD, 2000-03-01}
 Assets:Foo 2000.00 STOCK {0.25 USD, 2000-02-01}
 Assets:Foo 2000.00 STOCK {0.3 USD, 2000-03-01}\
'''

    txn = entries[-4]
    assert isinstance(txn, Transaction)
    assert txn.date == datetime.date(2000, 5, 7)
    assert txn.narration == 'STOCK.B split 2:1'
    f = io.StringIO()
    printer.print_entry(txn, file=f)
    text = '\n'.join(sorted(filter(None, re.sub(r' +', ' ', f.getvalue()).split('\n')[1:])))
    assert text == '''\
 Assets:Bar -1 STOCK.B {1 USD, 2000-05-03}
 Assets:Bar 2 STOCK.B {0.5 USD, 2000-05-03}\
'''

@pytest.mark.parametrize('text', [
    '2000-05-01 custom "autobean.stock_split" STOCK',
    '2000-05-01 custom "autobean.stock_split" 10',
    '2000-05-01 custom "autobean.stock_split"',
])
def test_invalid(text: str) -> None:
    _, errors = load(text)
    assert errors
