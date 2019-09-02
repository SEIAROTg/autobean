# autobean.narration

Generate transaction narration from posting narration.

# Behavior

* For each transaction, its narration (if present and non-empty) and its postings' narration (if present and non-empty) will be joined with the delimiter ` | ` to form the new transaction narration.
* All non-transaction directives will remain unchanged.
* Posting narration will be taken from their `narration` metadata attributes (if present), or alternatively from inline comments starting with `;;` (if present and `narration` attribute is not present).
* The `narration` attributes will not be removed by this plugin.
* Spaces at the start or the end of posting narrations will be trimmed.
* In comment mode, narration is considered end at the first `;` and anything afterwards are treated as regular comments.

# Examples

```beancount
plugin "autobean.narration"

2000-01-01 open Assets:BankOfBean
2000-01-01 open Expenses:Beans:Soybeans
2000-01-01 open Expenses:Beans:Peas
2000-01-01 open Expenses:Delivery

; This results in a empty narration
2000-01-01 *
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
    Expenses:Beans:Peas                        50.00 USD

; This results in the narration "bean party"
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
    Expenses:Beans:Peas                        50.00 USD

; This results in the narration "bean party | soybean | pea"
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
        narration: "soybean"
    Expenses:Beans:Peas                        50.00 USD
        narration: "pea"

; This results in the narration "soybean | pea"
2000-01-01 *
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
        narration: "soybean"
    Expenses:Beans:Peas                        50.00 USD
        narration: "pea"

; This results in the narration "bean party | soybean | pea"
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD ;; soybean
    Expenses:Beans:Peas                        50.00 USD ;; pea ; comments
```
