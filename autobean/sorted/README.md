# autobean.sorted

Checks that transactions are in non-descending order in each file.

This helps manually locating a specific transaction and avoiding wrong date for copied transactions.

# Usage

To use the plugin:

```beancount
plugin "autobean.sorted"
```

To temporarily disable the check:

```beancount
1970-01-01 custom "autobean.sorted.enabled" FALSE
...
1970-01-01 custom "autobean.sorted.enabled" TRUE
```

Unlike many other directives, the `autobean.sorted.enabled` directive applies to directives based on their location (line number and file name) instead of their date. This is similar to `pushtag` / `poptag`. It has file-scope so the re-enabling is not necessary if the whole file is to be exempted from the check.


# Example

```beancount
plugin "autobean.sorted"

; We'd like most directives to be in non-descending order.

2021-01-01 *
  ...
2021-01-01 *
  ...
2020-01-03 *  ; <- error
  ...
2021-01-03 *
  ...
2021-01-04 *
  ...

; However, in some cases it's less desired, for example, paddings:

2021-02-01 pad ...
2021-02-02 balance ...

2021-02-01 pad ...  ; <- error
2021-02-02 balance ...

; To fix that, we could temporarily disable the check:

1970-01-01 custom "autobean.sorted.enabled" FALSE

2021-02-01 pad ...
2021-02-02 balance ...

2021-02-01 pad ...  ; <- now good
2021-02-02 balance ...

1970-01-01 custom "autobean.sorted.enabled" TRUE
```
