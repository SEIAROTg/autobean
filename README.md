# autobean
[![CircleCI](https://circleci.com/gh/SEIAROTg/autobean.svg?style=shield)](https://circleci.com/gh/SEIAROTg/autobean)
[![pypi](https://img.shields.io/pypi/v/autobean)](https://pypi.org/project/autobean/)
[![codecov](https://codecov.io/gh/SEIAROTg/autobean/branch/master/graph/badge.svg)](https://codecov.io/gh/SEIAROTg/autobean)
[![Maintainability](https://api.codeclimate.com/v1/badges/65e79b66e57139ed8bd0/maintainability)](https://codeclimate.com/github/SEIAROTg/autobean/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/65e79b66e57139ed8bd0/test_coverage)](https://codeclimate.com/github/SEIAROTg/autobean/test_coverage)
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
