# `autobean.share`

A beancount plugin to ease expense split, joint bookkeeping, and debt management for personal use cases.

## Usage

1. Installation
    ```sh
    pip install autobean
    ```
2. Enable the plugin and declare viewpoint
    ```beancount
    ; Let's look at things from Alice's viewpoint
    plugin "autobean.share" "Alice"
    ```
3. (Optional) define the default ownership structure
    ```beancount
    ; By default, Alice owns everything in this ledger.
    2000-01-01 * custom "autobean.share.policy" "default"
        share-Alice: 1

    ; Some recommended settings.
    2000-01-01 * custom "autobean.share.policy" "Assets:*"
        share-Alice: 1
        share_enforced: TRUE
        share_prorated_included: FALSE
    ```
4. Describe things from the overall viewpoint
    ```beancount
    ; From the overall viewpoint
    2000-01-01 *
        ; Alice paid 20 USD
        Assets:Bank                  -20.00 USD
        ; For Bob to watch a movie
        Expenses:Movie                20.00 USD
            share-Bob: 1
    ```
5. This is automatically transformed into:
    ```beancount
    ; From Alice's viewpoint
    2000-01-01 *
        ; Alice paid 20 USD
        Assets:Bank                  -20.00 USD
        ; Bob owes her 20 USD
        Assets:Receivables:Bob        20.00 USD
    ```

Note:
* The name of each party must be capitalized. This is to differentiate with special viewpoints (e.g. `everyone`).

## The viewpoint

Viewpoint decides from what perspective the input is projected into the output. Usually it is a name matching the `share-*` meta, for example, Alice in the example above. In addition to that, there are also two special viewpoints: `nobody` and `everyone`. The output will looks like the following respectively, all generated from the two postings we wrote above:

```beancount
; Alice
2000-01-01 *
    Assets:Bank                  -20.00 USD
    Assets:Receivables:Bob        20.00 USD

; Bob
2000-01-01 *
    Assets:Receivables:Alice     -20.00 USD
    Expenses:Movie                20.00 USD

; nobody
2000-01-01 *
    Assets:Bank                  -20.00 USD
    Expenses:Movie                20.00 USD
    Assets:Receivables:Alice     -20.00 USD
    Assets:Receivables:Bob        20.00 USD

; everyone
2000-01-01 *
    Assets:Bank:[Alice]          -20.00 USD
    Expenses:Movie:[Bob]          20.00 USD
    Assets:Receivables:Alice     -20.00 USD
    Assets:Receivables:Bob        20.00 USD
```

You may notice there are square brackets in the `everyone` viewpoint, this is to flag them not being real accounts and avoid users from accidentally posting into those accounts, as that is NOT valid beancount syntax.

## Ownership definition

### Posting policy

This is the basic way to define ownership, that is to put `share-*` meta under postings:

```beancount
2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Expenses:Movie                20.00 USD
        share-Bob: 1
```

### Transaction policy

Sometimes there are repetition across multiple postings in a single transaction as well. Let's also simplify it:

```beancount
2000-01-01 *
    share-Alice: 1
    share-Bob: 1
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Expenses:Groceries:Meat       10.00 USD
    Expenses:Groceries:Fruit       5.00 USD
    Expenses:Groceries:Veg         5.00 USD
```

Transaction level policies can be overridden by account level policies or posting level policies. Named policies can also be used at transaction level.

### Account policy

The ownership of some accounts almost never change. Having to repeat it in every posting is such a waste of effort. Let's simplify it:

```beancount
; Define policy at account opening
2000-01-01 open Assets:Bank
    share-Alice: 1
    share-Bob: 1

; Alternatively, define / update policy afterwards
2000-01-01 custom "autobean.share.policy" Assets:Bank
    share-Alice: 1
    share-Bob: 1

2000-01-01 *
    Assets:Bank                  -20.00 USD
    Expenses:Movie                20.00 USD
        share-Bob: 1
```

Account level policies can be overridden by posting level policies. Account level policies take effect at the beginning of its date, and may be changed later.

### Wildcard account policy

Sometimes we want the same policy to apply on many accounts, in which case we can use wildcard:

```beancount
2000-01-01 custom "autobean.share.policy" "Expenses:*"
    share-Alice: 1
    share-Bob: 1

2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Expenses:Groceries            20.00 USD
```

The wildcard must end with `":*"` for efficient lookup. Wildcard account policies can be overridden by account level or posting level policies. A wildcard account policy on `Assets:Bank:*` includes `Assets:Bank` itself.

### Named policy

There are also some ownership structures that are repeatedly used but not on fixed accounts. Let's also simplify it:

```beancount
2000-01-01 custom "autobean.share.policy" "AA"
    share-Alice: 1
    share-Bob: 1

2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Expenses:Groceries            20.00 USD
        share_policy: "AA"
```

Policy name must not contain colons or asterisk to differentiate with wildcard account policy. Named policies can also be used to define account policies or wildcard account policies.

### Default policy

There can also be a global default, defined as:

```beancount
2000-01-01 custom "autobean.share.policy" "default"
    share-Alice: 1
    share-Bob: 1

2000-01-01 *
    Assets:Bank                  -20.00 USD
        share-Alice: 1
    Expenses:Groceries            20.00 USD
```

### Overrides

The policy lookup order is: posting > account > wildcard account > transaction > default. When a named policy is encountered, the lookup will immediately end in favor of that named policy.

References to named policies are pointers, not copies. That is, an update in a named policy is automatically reflected in other policies referencing it.

Ownership overrides are complete overwrites: if `share-Alice: 1; share-Bob: 2` is overridden by `share-Bob: 1`, it marks Bob as the sole owner, instead of 1:1 split between Alice and Bob.

Options are overridden separately: if `share-Alice: 1; share_conversion: FALSE` is overridden by `share-Bob: 1`, the `share_conversion: FALSE` is still inherited. However, if it's overridden by `share_policy: "foo"` where `foo` is `share-Bob: 1`, the `share_conversion: FALSE` will be dropped. Note that `share_prorated` counts as ownership instead of option.

# Rationale

See [docs/rationale.md](docs/rationale.md).

# Advanced Topics

See [docs/advanced.md](docs/advanced.md).

# Tips

## External accounts

If you have some recurring "pay for others" situation where the exact expense isn't interesting to you, for example buying reimbursable work stuff, it may be simplified by having a dedicated account:

```beancount
2000-01-01 open Expenses:External:MyCompany
    share-MyCompany: 1

2000-01-01 * "buy work stuff" ^foo
    Assets:Bank                  -20.00 USD
    Expenses:External:MyCompany

2000-01-01 * "reimbursement" ^foo
    Expenses:External:MyCompany
    Assets:Bank                   20.00 USD
```

There is nothing special about the naming of that account. It's simply a random account with share policy attached to it.

## Viewpoint switch

fava supports serving multiple ledgers, and we can use that for viewpoint switch.

```beancount
; alice-viewpoint.bean

option "title" "Alice"
plugin "autobean.share" "Alice"
include "main.bean"

; everyone-viewpoint.bean

option "title" "everyone"
plugin "autobean.share" "everyone"
include "main.bean"
```

Then start fava wtih `fava alice-viewpoint.bean everyone-viewpoint.bean`, you'll see a drop down in the top left, which allows us to switch between Alice and everyone.

## Limitation

* This plugin assumes receivables and payables can always cancel each other, which is usually fine for personal use but may sometimes be inappropriate.
* Currently there isn't a way to map different names and account names across multiple included ledgers (e.g. Alice may be called "Me" in her personal ledger but "Mom" in the family ledger).
