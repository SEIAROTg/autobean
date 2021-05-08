# autobean.narration

Generates transaction narration from posting narration and posting narration from comments.

# Behavior

* For each transaction with no narration or empty narration, its postings' narration (if present and non-empty) will be joined with the delimiter ` | ` to form the new transaction narration.
* Posting narration will be taken from their `narration` metadata (if present).
* A posting's `narration` metadata, if missing, will be populated from its inline comments starting with `;;`, if present.
* Spaces at the start or the end of posting narrations will be trimmed.
* All non-transaction directives will remain unchanged.
* In comment mode, narration is considered end at the first `;` and anything afterwards are treated as regular comments.

# Examples

```beancount
plugin "autobean.narration"

2000-01-01 open Assets:BankOfBean
2000-01-01 open Expenses:Beans:Soybeans
2000-01-01 open Expenses:Beans:Peas
2000-01-01 open Expenses:Delivery

; The transaction narration remains unchanged (already specified)
; The posting narrations are populated from comments
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD ;; soybean
    ; narration: "soybean"  <- this will be populated from comment
    Expenses:Beans:Peas                        50.00 USD ;; pea ; comments
    ; narration: "pea"      <- this will be populated from comment

; The transaction narration will be "soybean | pea"
; The posting narrations remain unchanged (already in metadata)
2000-01-01 *
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
        narration: "soybean"
    Expenses:Beans:Peas                        50.00 USD
        narration: "pea"

; This remains unchanged (no narration)
2000-01-01 *
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
    Expenses:Beans:Peas                        50.00 USD

; This remains unchanged (transaction narration present, no posting narration)
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
    Expenses:Beans:Peas                        50.00 USD

; This remains unchanged (transaction narration present, posting narration in metadata)
2000-01-01 * "bean party"
    Assets:BankOfBean                        -110.00 USD
    Expenses:Delivery                          10.00 USD
    Expenses:Beans:Soybeans                    50.00 USD
        narration: "soybean"
    Expenses:Beans:Peas                        50.00 USD
        narration: "pea"
```
