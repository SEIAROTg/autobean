# `autobean.include`

Include external beancount ledgers without disabling their plugins.

# Behavior

The built-in `include` directive merely includes the directives in external ledgers without executing their plugins. This plugin, conversely, includes them as transformed by their plugins.

* `autobean.include` directives in included ledgers will not be processed unless they enable this plugin as well.
* The date of `autobean.include` directive is ignored.

# Examples

```beancount
; source.beancount

plugin "autobean.include"

2000-01-01 custom "autobean.include" "external.beancount"
```

```beancount
; external.beancount

plugin "beancount.plugins.exclude_tag"

2000-01-01 open Assets:BankOfBean
2000-01-01 open Expenses:Bean

2000-01-01 *
    Assets:BankOfBean                        -100.00 USD
    Expenses:Bean                             100.00 USD

2000-01-02 * #virtual
    Assets:BankOfBean                        -100.00 USD
    Expenses:Bean                             100.00 USD
```

```beancount
; source.beancount (results)

2000-01-01 open Assets:BankOfBean
2000-01-01 open Expenses:Bean

2000-01-01 *
    Assets:BankOfBean                        -100.00 USD
    Expenses:Bean                             100.00 USD
```