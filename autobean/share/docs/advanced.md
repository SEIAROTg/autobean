# `autobean.share`: Advanced Topics

The principle behind `autobean.share` is simple, but the real world is always full of complications.

## Split postings

What if the money comes from a joint account, contributed 1:1 by Alice and Bob? Who owns the Asset posting then?

The single-owner model above hits its limitation here, but we can easily generalize it into something like this:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
        share-Bob: 1
    Expenses:Movie                20.00 USD
        share-Bob: 1
```

This can also be easily adopted for split expenses.

## Prorated distribution

Consider this case:

```beancount
2000-01-01 *
    Assets:Bank                  -90.00 USD
        share-Alice: 1
    Expenses:Meal                 20.00 USD
        share-Alice: 1
    Expenses:Meal                 25.00 USD
        share-Bob: 1
    Expenses:Meal                 30.00 USD
        share-Charlie: 1
    Expenses:ServiceCharge        15.00 USD
        ; ???
```

Who should liable for the service charge? `1:1:1` is a trivial solution but sometimes we want it to be distributed based on the actual expenses, that is `20:25:30`. Can we do that easily?

We can mark the service charge with `share_prorated: TRUE` and hand over to the automation.

But wait, how does automation know the `Assets:Bank` posting is not part of the game? Because it's a balance sheet account? What if we are not buying `Expenses:Meal` but buying `Assets:House`? Because the amount has a different sign? What if there is a discount for Alice which is also negative?

The solution this plugin presents is to attach a `share_prorated_included: FALSE` under the `Assets:Bank` posting. To make life easier, it can be added to the `Assets:*` wildcard account policy.

Also, to make it work, all participating postings must have the same currency, though it doesn't have to match the currency of the `share_prorated: TRUE` posting.

## Currency conversion

Consider the following transaction:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD @@
        share-Alice: 1
    Expenses:Movie                15.00 GBP
        share-Bob: 1
```

From Alice's viewpoint it will be:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD @@
    Assets:Receivables:Bob        15.00 GBP
```

Alice did a favor for Bob but the forex risk is now on her side. That is not fair. While this is sometimes fine, it would be nice if Alice has the option to avoid it.

We can easily fix the above example by shifting `@@` to Bob side, but that doesn't work when Bob buys multiple items.

We can always do this but it would also be nice to avoid that redundancy:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD @ 0.75 GBP
        share-Alice: 1
    Expenses:Movie                15.00 GBP
        share-Bob: 1
    Assets:Receivables:Bob       -15.00 GBP
    Assets:Receivables:Bob        20.00 USD @ 0.75 GBP
```

Essentially, there is a choice to make between conversion first or loan first, that is, to differentiate between:

```beancount
; conversion first
2000-01-01 *
    Assets:Bank                  -20.00 USD @@
    Assets:Receivables:Bob        15.00 GBP

; loan first
2000-01-01 *
    Assets:Bank                  -20.00 USD @@ 15.00 GBP
    Assets:Receivables:Bob        20.00 USD @@ 15.00 GBP
```

Because the receivable account isn't part of our input, the `@` conversion will always be attached to the `Assets:Bank` side. Some additional information is therefore required to make that choice, which, in this plugin, is the `share_conversion` meta:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD @@
        share-Alice: 1
        share_conversion: FALSE
    Expenses:Movie                15.00 GBP
        share-Bob: 1
```

This will yield:

```beancount
; Alice
2000-01-01 *
    Assets:Bank                  -20.00 USD @@ 15.00 GBP
    Assets:Receivables:Bob        20.00 USD @@ 15.00 GBP

; Bob
2000-01-01 *
    Assets:Receivables:Alice     -20.00 USD @@
    Expenses:Movie                15.00 GBP

; everyone
2000-01-01 *
    Assets:Bank:[Alice]          -20.00 USD @@ 15.00 GBP
    Expenses:Movie:[Bob]          15.00 GBP
    Assets:Receivables:Bob        20.00 USD @@ 15.00 GBP
    Assets:Receivables:Alice     -20.00 USD @@ 15.00 GBP
```

However, this may only be used under unambiguous circumstance. If Alice paid `50 USD @ 1.25 GBP`, Bob paid `60 USD @ 1.2 GBP`, Charlie spent `30 USD`, and Delta spent `60 USD`, who should use which rate becomes difficult for the automation to decide.

This plugin therefore requires that if a posting has `share_conversion: FALSE`, there must be a unique way in the transaction to convert to its cost / price currency. For example, if a posting `-20.00 USD @ 0.75 GBP` has `share_conversion: FALSE`, any other postings must either not have `GBP` as their cost / price currency or must use the identical conversion rate and as a result, all `GBP` in receivable postings will be converted to `USD @ 0.75 GBP`.

## Balance assertion

Think about the following ledger:

```beancount
2000-01-01 *
    Assets:Bank:Alice            -20.00 USD
        share-Alice: 1
    Assets:Bank:Joint             20.00 USD
        share-Alice: 1
        share-Bob: 1

2000-01-01 *
    Assets:Bank:Alice            -10.00 USD
        share-Alice: 1
    Assets:Bank:Joint             10.00 USD
        share-Alice: 1

2000-01-02 balance Assets:Bank:Alice -30.00 USD ; pass
2000-01-02 balance Assets:Bank:Joint  30.00 USD ; pass
2000-01-02 balance Assets:Bank:Joint  20.00 USD ; fail
```

How should it look like from the Alice's viewpoint? Let's try:

```beancount
2000-01-01 *
    Assets:Bank:Alice            -20.00 USD
    Assets:Bank:Joint             10.00 USD
    Assets:Receivables:Bob        10.00 USD

2000-01-01 *
    Assets:Bank:Alice            -10.00 USD
    Assets:Bank:Joint             10.00 USD

2000-01-02 balance Assets:Bank:Alice -30.00 USD
2000-01-02 balance Assets:Bank:Joint     ?? USD
2000-01-02 balance Assets:Bank:Joint     ?? USD
```

The first balance assertion looks easy as Alice owns 100% of her bank account.

What about the second one? Keeping `30.00 USD` is apparently wrong as it makes a passing assertion fail. `20.00 USD`  will let it pass but that is in no way related to our original balance directive, which defeats the purpose of having such assertion. That "making it pass" strategy is even more wrong for the third assertion, which shouldn't even pass.

Let's now consider the semantics of account balance from each viewpoint:

* From the overall viewpoint, it's the total amount of money held in the account.
* From Alice's viewpoint, it's the share of money in the account that truely belongs to Alice.

If we make an assertion on the total amount, does it imply any assertion on Alice's share? Probably not, unless when they are equivalent, or in another word Alice is the sole owner of the account.

This concludes none of the balance assertion from Alice's ledger actually make sense, even the first one, because Alice being the sole owner of `Assets:Bank:Alice` is not apparent with only some share policy at posting level. Even if the share policy were defined on the account, nothing prevents overrides at posting levels.

However, in practice we do want balance assertions — they help us build confidence (by creating errors on failure) and allows us to easily find out when the balance was last verified (by showing up in fava). How can we bridge the gap?

To bring back the check, we could simply perform the check before switching the viewpoint, so errors can be caught. This plugin always does that.

To preserve the balance directives, given the source of problem was that Alice being the sole account owner is not clear, we could just add that information. The way to do that in this plugin is  `share_enforced: TRUE` in share policy at account or global level (but not transaction or posting level, which does not make sense). This enforces the ownership structure by disallowing overrides at posting or transaction level. For example:

```beancount
2000-01-01 * custom "autobean.share.policy" Assets:Bank:Alice
    share-Alice: 1
    share_enforced: TRUE

2000-01-01 *
    Assets:Bank:Alice            -20.00 USD
    Assets:Bank:Joint             20.00 USD
        share-Alice: 1
        share-Bob: 1

2000-01-01 *
    Assets:Bank:Alice            -10.00 USD
    Assets:Bank:Joint             10.00 USD
        share-Alice: 1

2000-01-02 balance Assets:Bank:Alice -30.00 USD ; pass
2000-01-02 balance Assets:Bank:Joint  30.00 USD ; pass
2000-01-02 balance Assets:Bank:Joint  20.00 USD ; fail
```

This will yields the following from Alice's viewpoint:

```beancount
; error: balance failure on <input>:18

2000-01-01 *
    Assets:Bank:Alice            -20.00 USD
    Assets:Bank:Joint             10.00 USD
    Assets:Receivables:Bob        10.00 USD

2000-01-01 *
    Assets:Bank:Alice            -10.00 USD
    Assets:Bank:Joint             10.00 USD

2000-01-02 balance Assets:Bank:Alice -30.00 USD
```

This can even work when Alice isn't the sole owner, as long as the ownership structure is clear, in which case the balance can be split proportionately.

## Proportionate assertion

Sometimes we may want to assert the balance of certain accounts are shared proportionately, without caring about how much it is exactly. For example, flatmates taking turns to top up their electricity meter may wish to assert that they all paid the same.

This can be done with:

```beancount
2000-01-01 * custom "autobean.share.proportionate" Assets:Electricity
```

## Shared ledger

Suppose Alice and Bob are flatmates, they may want to collectively maintain a ledger for household expenditure, while also keeping their personal ones separately. It would be nice to avoid having to book the same things twice. How can we do that?

```beancount
; household.bean

2000-01-01 *
    Assets:Bank:Alice            -50.00 USD
        share-Alice: 1
    Expenses:Movie                40.00 USD
        share-Alice: 1
        share-Bob: 1
    Expenses:Popcron              10.00 USD
        share-Alice: 1

; alice.bean

plugin "autobean.share" "Alice"
2000-01-01 custom "autobean.share.include" "household.bean"

; bob.bean

plugin "autobean.share" "Bob"
2000-01-01 custom "autobean.share.include" "household.bean"
```

`autobean.share.include` is different from the builtin `include` directive in that it is hierarchical:

* Plugins are evaluated inside the included ledgers.
* Share policies are scoped inside the included ledger.
* Receivable account name and viewpoint are determined by the outermost ledger.

## Scope and privacy in shared ledger

Suppose Alice and Bob maintains a joint ledger, Alice probably doesn't want Bob to know all bank accounts or card she have, or exactly which payment method was used in each payment. Or even without privacy concern, having to match accounts between the shared ledger and personal ones can be a maintenance burden in making sure they match after changes, avoiding conflicts, etc..

What can we do to make life easier? Since the shared ledger doesn't have to know what exact payment method was used, maybe we could remove that information? What about this?

```beancount
; household.bean

2000-01-01 *
    Assets:External:Alice        -50.00 USD ; we don't care exactly what bank
        share-Alice: 1
    Expenses:Movie                40.00 USD
        share-Alice: 1
        share-Bob: 1
    Expenses:Popcron              10.00 USD
        share-Alice: 1
```

But Alice does want to track the payment method, so she will have a transaction in her personal ledger. But what postings should be their to balance the transaction? Having to repeat all the itemized expenses is such a redundancy and defeats the purpose of this plugin.

```beancount
; alice.bean

2000-01-01 *
    Assets:BoA:Checking          -50.00 USD
    ; what do we put here?
```

With this plugin, Alice can simply put a mark posting there, which will be automatically cancelled with the `Assets:External:Alice` posting in the joint ledger:

```beancount
; alice.bean

2000-01-01 *
    Assets:BoA:Checking          -50.00 USD
    Assets:External:Joint
        share-Joint: 1

; alice-view.bean

2000-01-01 custom "autobean.share.include" "household.bean"
2000-01-01 custom "autobean.share.include" "alice.bean"
2000-01-01 custom "autobean.share.link" "household.bean" Assets:External:Alice "alice.bean" Assets:External:Joint
```

With that, Alice will be able to see the following from `alice-view.bean`, which has everything Alice is interested in:

```beancount
2000-01-01 *
    Assets:BoA:Checking          -50.00 USD
    Expenses:Movie                30.00 USD
    Assets:Receivables:Bob        20.00 USD
    Expenses:Popcron              10.00 USD
```

The link resolution is based on some heuristics which may not always produce the correct result. In case it doesn't work well, one can manually link two transactions by attaching a same string in the `share_link_key` meta.

## Custom receivable accounts

By default all receivables **and payables** goes to `Assets:Receivables:{name}`. If this doesn't match your account structure, it can be customized with:

```beancount
2000-01-01 custom "autobean.share.receivable-account" Liabilities:Payables
```

## Rounding

Rounding can also be painful sometimes. Consider the following transaction:

```beancount
2000-01-01 *
    Assets:Bank:Alice           -100.00 USD
    Expenses:Meal                100.00 USD
        share-Alice: 1
        share-Bob: 1
        share-Charlie: 1
```

How should that `100.00 USD` expense be distributed across the three beneficiaries?

* Each get `33⅓`.
    * That is theoretically accurate.
    * But it's not expressable in Python `decimal.Decimal` and thus not in beancount.
    * It creates a challenge to display in fava.
* Each get `33.33`.
    * The transaction doesn't balance.
* Each get `33.33`, `33.33`, and `33.34`.
    * How do we make it fair so the extra `0.01` doesn't always hurt the same people?
    * How do we make it stable so that an innocent change (e.g. date change, posting reorder) doesn't affect the distribution and existing balance assertions?
* Each get `decimal.Deciaml('100.00') / 3`
    * People will commonly see lots of decimal places on fava, and it breaks tolerance calculation.
    * The transaction doesn't really balance with a tiny gap: `D(100) - D(100) / 3 * 3 == D('1E-26')`.
        * It is so small that will very unlikely to accumulate to even `0.01 USD` in anyone's whole lifetime, and beancount does recognize it as balanced because that is within the tolerance.
        * However, ideally we could fix it, especially since this is an unfair systematic loss on whoever made the payment.

I really don't have a good solution here so I chose the last option which looks the least broken.

## Who owns the receivables?

You might wonder, if every account has an ownership structure, who owns the generated receivables?

It's fairly clear when there are only two persons: Alice owns `Assets:Receivables:Bob` and Bob owns `Assets:Receivables:Alice`. But what if there are three persons, say, plus Charlie?

Actually, nobody owns a receivable account, or everyone else collectively owns a receivable accounts. What Alice actually owns is her payables, which is the opposite of `Assets:Receivables:Alice`, but showing that to Alice is not very useful: ok, I know I owe that amount of money, but to whom?

To make it more useful, this plugin decides to replace `-Assets:Receivables:Alice` with `Assets:Receivables:Bob + Assets:Receivables:Charlie`. This is possible because all receivables add up to zero, as they are all generated on top of already-balanced transactions. The sacrifice, is that this adds another layer of indirection, making receivable acccounts less uniform with others (e.g. not splitable) and slightly harder to reason about.

## Working with generated accounts

The receivable accounts and subaccounts (only in `everyone` viewpoint, e.g. `Expenses:Movie:[Bob]`) are generated. While they do show accurate information, interacting them without going through this plugin is a slightly different story.

### Post into subaccounts

People should never directly post into a subaccounts, which can cause receivables to be calculated incorrectly. In fact, nobody should ever need to do this:

```beancount
; This is wrong!
    Expenses:Movie:[Bob]          20.00 USD

; Do this:
    Expenses:Movie                20.00 USD
        share-Bob: 1
```

For that reason, subaccounts have square brackets in their name, making it unparsable when people try to post stuff directly into them.

### Post into receivable accounts

In contrast to subaccounts, there are good reasons for people to directly post into receivable accounts. For example, Alice and Bob agree to convert all the debt from USD to GBP:

```beancount
2000-01-01 *
    Assets:Receivables:Bob       -20.00 USD
    Assets:Receivables:Bob        16.00 GBP @@
```

You might think this is doable through this plugin with something like this:

```beancount
; This is wrong!

2000-01-01 *
    Assets:External:Bob          -20.00 USD
        share-Bob: 1
    Assets:External:Bob           16.00 GBP @@
        share-Bob: 1
```

However, as far as this plugin is concerned, this means Bob himself exchanged $20 for £15, which has nothing to do with Alice. That does make sense as nowhere is Alice mentioned in this transaction.

Therefore, receivable accounts are exposed for manual postings.

There is still a question though: whose receivables are we making changes to? `Assets:Receivables:Bob` denotes Bob owes something to someone else, but who? Similar to other accounts, we can mark its ownership through share policy:

```beancount
2000-01-01 *
    share-Alice: 1
    share-Charlie: 1
    Assets:Receivables:Bob       -20.00 USD
    Assets:Receivables:Bob        16.00 GBP @@
```

One key difference from operating on regular accounts is that receivable accounts won't be further split into `Assets:Receivables:Bob:[Alice]` and `Assets:Receivables:Bob:[Charlie]`, and in the `everyone` viewpoint, the above transaction will be represented as follows:

```beancount
2000-01-01
    Assets:Receivables:Bob       -20.00 USD
    Assets:Receivables:Alice      10.00 USD
    Assets:Receivables:Charlie    10.00 USD
    Assets:Receivables:Bob        16.00 GBP @ 1.25 USD
    Assets:Receivables:Alice      -8.00 GBP @ 1.25 USD
    Assets:Receivables:Charlie    -8.00 GBP @ 1.25 USD
```

## Share policy on receivable accounts

One might wonder, what does the following transactions mean:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Assets:Receivables:Bob        20.00 USD
        share-Bob: 1
```

The intention seems to be have Bob repay Alice later but that notation apparently suggests Bob is the sole owner of that receivable? How could that be right?

It's not. The receivables are always owned by whoever owns the ledger. What Bob has is the payable which is the complement to receivable.

Therefore, share policies on receivable accounts (or postings related to receivable accounts) do not make sense and are disallowed.

## Balance assertion on generated accounts

While posting into generated accounts are easy, balance assertions aren't, because those accounts simply don't exist or are incomplete before the viewpoint is applied. How could we make assertions then? We do intent to make assertions on the receivables after the viewpoint is applied, but that will almost certainly fail without this plugin. Can we avoid this?

To support that, this plugin allows "deferred" balance assertion, which is only checked after the plugin is evaluated, while being no-op before that:

```beancount
2000-01-01 custom "autobean.share.balance" Assets:Receivables:Bob 20.00 USD
; which translates into
; 2000-01-01 balance Assets:Receivables:Bob 20.00 USD

2000-01-01 custom "autobean.share.balance" Assets:Receivables:Bob 20.00 USD 0.01
; which translates into
; 2000-01-01 balance Assets:Receivables:Bob 20.00 ~ 0.01 GBP

2000-01-01 custom "autobean.share.balance" "Assets:Bank:[Alice]" -20.00 GBP
; which translates into
; 2000-01-01 balance Assets:Bank:[Alice] -20.00 GBP
```

For safety reason, this plugin will create errors on any existing balance assertions on receivable accounts. This might be disruptive to your transactions before using this plugin, which can be fixed by surrounding them with:

```beancount
; balance on receivable accounts are forbidden

2000-01-01 custom "autobean.share.enable" FALSE

; balance on receivable accounts are permitted

2020-01-01 custom "autobean.share.enable" TRUE

; balance on receivable accounts are forbidden
```

## Pad on generated accounts

Similar to balances, pad on generated accounts directly can go very wrong. The solution is also similarily a deferred pad:

```beancount
2000-01-01 custom "autobean.share.pad" Assets:Receivables:Bob Expenses:Loss
2000-01-02 custom "autobean.share.balance" Assets:Receivables:Bob 0.00 USD
```

Again, for safety reason, direct pad on generated accounts will create error, which can be fixed by disabling this plugin for the relevant directives.
