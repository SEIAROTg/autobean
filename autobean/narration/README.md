# autobean.narration

Generate transaction narration from postings' `narration` metadata attribute.

# Behavior

For each transaction, its narration (if present and non-empty) and its postings' `narration` metadata attributes (if present and non-empty) will be joined with the delimiter ` | ` to form the new transaction narration. The `narration` metadata will not be removed. All non-transaction directives will remain unchanged.

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
```
