# `autobean.xcheck`

Cross-check against external ledgers.

## Behavior

This plugins checks if all postings in the current ledger appear in an external ledger and vice versa, in terms of their date, account and amount.

* Balance assertions in the external ledger will be applied on the current ledger.
* Only postings on concerned accounts whose date fall in the specified time period are compared.
* If concerned accounts are not specified, it defaults to any accounts. 
* This plugin does not compare any unmentioned properties such as payee and narration of transactions, or cost of postings.
* This plugin only compares at posting level and does not check whether postings are grouped into same transactions.
* `ValidationError` occured when loading the external ledger will be suppressed so you don't have to balance bank statements.

## Examples

```beancount
; source.beancount

plugin "autobean.xcheck"

2000-01-01 open Assets:BankOfBean:DebitCard
2000-01-01 open Expenses:Bean

2000-01-01 !
    Assets:BankOfBean:DebitCard              -100.00 USD
    Expenses:Bean                             100.00 USD

; Cross-check against `statements/200001.beancount`, for any postings between 2000-01-01 (inclusive) and 2000-02-01 (exclusive)
2000-02-01 custom "autobean.xcheck" "statements/200001.beancount" 2000-01-01

; Cross-check against `statements/200001.beancount`, for any postings on either Assets:BankOfBean:DebitCard or Assets:BankOfBean:CreditCard and between 2000-01-01 (inclusive) and 2000-02-01 (exclusive) 
2000-02-01 custom "autobean.xcheck" "statements/200001.beancount" 2000-01-01 Assets:BankOfBean:DebitCard Assets:BankOfBean:CreditCard

```

```beancount
; statements/200001.beancount

option "plugin_processing_mode" "raw"

2000-01-01 !
    Assets:BankOfBean:DebitCard              -100.00 USD
```
