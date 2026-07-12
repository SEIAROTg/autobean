# autobean
[![build](https://github.com/SEIAROTg/autobean/actions/workflows/build.yml/badge.svg)](https://github.com/SEIAROTg/autobean/actions/workflows/build.yml)
[![pypi](https://img.shields.io/pypi/v/autobean)](https://pypi.org/project/autobean/)
[![Maintainability](https://qlty.sh/gh/SEIAROTg/projects/autobean/maintainability.svg)](https://qlty.sh/gh/SEIAROTg/projects/autobean)
[![Test Coverage](https://qlty.sh/gh/SEIAROTg/projects/autobean/coverage.svg)](https://qlty.sh/gh/SEIAROTg/projects/autobean)
[![license](https://img.shields.io/github/license/SEIAROTg/autobean.svg)](https://github.com/SEIAROTg/autobean)

A collection of plugins and scripts that help automating bookkeeping with [beancount](http://furius.ca/beancount/).

## Components

* [autobean.share](autobean/share): expense split, joint bookkeeping, and debt management for personal use cases.
* [autobean.xcheck](autobean/xcheck): Cross-checks against external ledgers.
* [autobean.narration](autobean/narration): Generates transaction narration from posting narration and posting narration from comments.
* [autobean.include](autobean/include): Includes external beancount ledgers without disabling their plugins.
* [autobean.truelayer](autobean/truelayer): Imports transactions from banks via [TrueLayer](https://truelayer.com/), a bank API aggregator.
* [autobean.sorted](autobean/sorted): Checks that transactions are in non-descending order in each file.
* [autobean.stock_split](autobean/stock_split): Simplifies stock split.

## Install

```sh
pip install autobean
```
