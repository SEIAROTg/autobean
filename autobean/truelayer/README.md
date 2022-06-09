# autobean.truelayer

Imports transactions from banks via [TrueLayer](https://truelayer.com/), a bank API aggregator.

# Set up

1. Create an account with [TrueLayer](https://truelayer.com/).
1. Create an app in live environment in TrueLayer console. You will be given a client id and a client secret in this step.
1. Configure `autobean.truelayer` in your beancount importer config. If you don't already have an importer config, create a `import_config.py` in your ledger directory with the following content:

    ```py
    import autobean.truelayer

    CONFIG = [
        autobean.truelayer.Importer(CLIENT_ID, CLIENT_SECRET),
    ]
    ```
1. Create an empty file ending with `.truelayer.yaml` in your ledger directory for each bank.
1. Run `bean-extract path/to/import_config.py path/to/bank.truelayer.yaml`
1. Following the popup browser window (or the printed link) to complete the authorization process.
1. You will see your recent transactions printed.

# Usage

After the initial setup, you might want to edit the `.truelayer.yaml` file to map your bank accounts to beancount accounts, disable accounts you would like to ignore or set the timestamp to start import. See Config section below.

With a proper config, you will be able to import transactions with `bean-extract` command. The authorization should typically be valid for 90 days after which the command will prompt for a re-authorization.

# Config

`.truelayer.yaml` files contain the following fields:

* `access_token`, `access_token_expiry_time`, `refresh_token`: TrueLayer OAuth credentials. Don't alter.
* `accounts`, `cards`: Maps from account ids (don't alter) to accounts, which contain the following fields
    * `beancount_account`: The corresponding beancount account name. Multiple accounts can be mapped into one beancount account. Balance assertions may not work correctly if they share common currencies.
    * `enabled`: If set to `false`, this account will be ignored.
    * `liability`: If set to `true`, the sign of account balance will be flipped.
    * `from`: A timestamp in seconds since which the transactions should be fetched.
    * `name`: A string for human to identify the account. Not consumed by the importer.
