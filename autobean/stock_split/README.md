# autobean.stock_split

Simplifies stock split.

# Usage

```beancount
{date} custom "autobean.stock_split" {multiplier} {commodity}
```

For example:

```
2000-05-01 custom "autobean.stock_split" 10 STOCK
```

This splits 1 STOCK into 10 STOCK.

# Example

```beancount
plugin "autobean.stock_split"

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
```

The custom directive will be replaced by:

```beancount
2000-05-01 * "STOCK split 10:1"
    Assets:Foo   -100.00 STOCK {5 USD, 2000-02-01}
    Assets:Foo   1000.00 STOCK {0.5 USD, 2000-02-01}
    Assets:Foo   -100.00 STOCK {6 USD, 2000-03-01}
    Assets:Foo   1000.00 STOCK {0.6 USD, 2000-03-01}
    Assets:Bar   -100.00 STOCK {6 USD, 2000-04-01}
    Assets:Bar   1000.00 STOCK {0.6 USD, 2000-04-01}
```
