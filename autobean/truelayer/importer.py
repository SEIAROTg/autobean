import datetime
from decimal import Decimal
import http.server
import logging
import os
import re
import time
import secrets
import sys
from typing import Any, Optional
import urllib.parse
import webbrowser

from autobean.utils import deduplicate
from beancount.core.amount import Amount
from beancount.core.data import Transaction, Posting, Balance, Directive, new_metadata
from beancount.core import inventory
from beancount.ingest import importer
from beancount.ingest import cache
import dateutil.parser
import requests
import yaml


CONFIG_SUFFIX = '.truelayer.yaml'
ACCOUNT_TYPES = ('accounts', 'cards')


def escape_account_component(s: str) -> str:
    s = re.sub(r'\W', '', s)
    s = s[:1].upper() + s[1:]
    return s


def format_iso_datetime(timestamp_s: float) -> str:
    return datetime.datetime.utcfromtimestamp(int(timestamp_s)).isoformat()


def currency_to_decimal(currency: float) -> Decimal:
    return Decimal(f'{currency:.2f}')


class Importer(importer.ImporterProtocol):

    def __init__(self, client_id: str, client_secret: str):
        self._client_id = client_id
        self._client_secret = client_secret

    def name(self) -> str:
        return 'autobean.truelayer'

    def identify(self, file: cache._FileMemo) -> bool:
        return file.name.endswith(CONFIG_SUFFIX)

    def extract(self, file: cache._FileMemo, existing_entries: Optional[list[Directive]] = None) -> list[Directive]:
        config = _Config(self._client_id, self._client_secret, file)
        extractor = _Extractor(config)
        return extractor.extract(existing_entries)


class _Config:
    def __init__(self, client_id: str, client_secret: str, file: cache._FileMemo):
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = yaml.safe_load(file.contents()) or {}
        self._filename = file.name

    @property
    def name(self) -> str:
        return os.path.basename(self._filename).rsplit(CONFIG_SUFFIX, 1)[0]

    def dump(self) -> None:
        with open(self._filename, 'w') as f:
            yaml.safe_dump(self.data, f)


class _Extractor:
    def __init__(self, config: _Config):
        self._config = config
        self._oauth_manager = _OAuthManager(config)

    def extract(self, existing_entries: Optional[list[Directive]] = None) -> list[Directive]:
        for type_ in ACCOUNT_TYPES:
            self._update_accounts(type_)
        entries = self._fetch_all_transactions()
        if existing_entries:
            entries = deduplicate.deduplicate(entries, existing_entries)
        return entries

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {
            'Authorization': f'Bearer {self._oauth_manager.access_token}'
        }

    def _update_accounts(self, type_: str) -> None:
        url = {
            'accounts': 'https://api.truelayer.com/data/v1/accounts',
            'cards': 'https://api.truelayer.com/data/v1/cards',
        }
        r = requests.get(url[type_], headers=self._auth_headers)
        if not r.ok:
            logging.warning('Could not fetch %s: %s', type_, r.text)
            return
        accounts = r.json().get('results', [])
        config_accounts = self._config.data.setdefault(type_, {})
        for account in accounts:
            config_account = config_accounts.setdefault(
                account['account_id'], {})
            config_account.setdefault('name', account['display_name'])
            config_account.setdefault(
                'liability',
                type_ == 'cards' and account['card_type'] == 'CREDIT')
            config_account.setdefault('enabled', True)
            config_account.setdefault('beancount_account', ':'.join([
                'Liabilities' if config_account['liability'] else 'Assets',
                escape_account_component(self._config.name),
                escape_account_component(config_account['name'])
            ]))
            config_account.setdefault('from', int(time.time()) - 86400 * 90)

        self._config.dump()

    def _fetch_transactions(
            self,
            account_id: str,
            account: dict[str, Any],
            type_: str,
            is_pending: bool) -> list[dict[str, Any]]:
        url = {
            ('accounts', False): (
                f'https://api.truelayer.com/data/v1/accounts/{account_id}/transactions'),
            ('accounts', True): (
                f'https://api.truelayer.com/data/v1/accounts/{account_id}/transactions/pending'),
            ('cards', False): (
                f'https://api.truelayer.com/data/v1/cards/{account_id}/transactions'),
            ('cards', True): (
                f'https://api.truelayer.com/data/v1/cards/{account_id}/transactions/pending'),
        }
        log_transaction = 'pending transactions' if is_pending else 'transactions'
        logging.info(
            f'Fetching {log_transaction} for account {account["name"]} '
            f'({account_id}).')
        r = requests.get(
            url[(type_, is_pending)],
            headers=self._auth_headers,
            params={
                'from': format_iso_datetime(account['from']),
                'to': format_iso_datetime(time.time()),
            }
        )
        if not r.ok:
            logging.error('Error fetching transactions: %s', r.text)
            r.raise_for_status()
        txns = r.json().get('results', [])
        logging.info(
            f'Fetched {len(txns)} {log_transaction} for account '
            f'{account["name"]} ({account_id}).')
        return txns

    def _fetch_balances(
            self,
            account_id: str,
            account: dict[str, Any],
            type_: str) -> list[dict[str, Any]]:
        url = {
            'accounts': f'https://api.truelayer.com/data/v1/accounts/{account_id}/balance',
            'cards': f'https://api.truelayer.com/data/v1/cards/{account_id}/balance',
        }
        logging.info(
            f'Fetching balance for account {account["name"]} ({account_id}).')
        r = requests.get(url[type_], headers=self._auth_headers)
        if not r.ok:
            logging.error('Error fetching balance: %s', r.text)
            r.raise_for_status()
        balances = r.json().get('results', [])
        logging.info(
            f'Fetched {len(balances)} balance entries for account '
            f'{account["name"]} ({account_id}).')
        return balances


    def _fetch_all_transactions(self) -> list[Directive]:
        entries: list[Directive] = []
        for type_ in ACCOUNT_TYPES:
            for account_id, account in self._config.data[type_].items():
                if not account['enabled']:
                    continue
                truelayer_txns = self._fetch_transactions(
                    account_id, account, type_, False)
                time_txns = [
                    (
                        dateutil.parser.parse(truelayer_txn['timestamp']),
                        self._transform_transaction(
                            truelayer_txn, account['beancount_account']))
                    for truelayer_txn in truelayer_txns
                ]
                pending_truelayer_txns = self._fetch_transactions(
                    account_id, account, type_, True)
                pending_time_txns = [
                    (
                        dateutil.parser.parse(truelayer_txn['timestamp']),
                        self._transform_transaction(
                            truelayer_txn, account['beancount_account'], True))
                    for truelayer_txn in pending_truelayer_txns
                ]
                entries.extend(txn for _, txn in time_txns)
                entries.extend(txn for _, txn in pending_time_txns)

                balances = self._fetch_balances(account_id, account, type_)
                for balance in balances:
                    entries.append(self._transform_balance(
                        balance, account, time_txns, pending_time_txns))
        return entries

    def _transform_balance(
            self,
            truelayer_balance: dict[str, Any],
            account: dict[str, Any],
            time_txns: list[tuple[datetime.datetime, Transaction]],
            pending_time_txns: list[tuple[datetime.datetime, Transaction]],
    ) -> Balance:
        """Transforms TrueLayer Balance to beancount Balance.
        
        Balance from TrueLayer can be effective at the middle of a day with
        pending transactions ignored, while beancount balance assertions
        must be applied at the beginning of a day and pending transactions
        are taken into account.

        It is not always possible to get pending transactions. If that is not
        available balance assertions may have to be corrected retrospectively.
        """

        balance_time = dateutil.parser.parse(
            truelayer_balance['update_timestamp']).astimezone()
        assertion_time = datetime.datetime.combine(
            balance_time, datetime.time.min, balance_time.tzinfo)

        txns_to_remove = [
            txn
            for t, txn in time_txns
            if assertion_time <= t < balance_time
        ]
        inventory_to_remove = inventory.Inventory()
        for txn in txns_to_remove:
            for posting in txn.postings:
                inventory_to_remove.add_position(posting)
        amount_to_remove = inventory_to_remove.get_currency_units(
            truelayer_balance['currency'])

        txns_to_add = [
            txn
            for t, txn in pending_time_txns
            if t < assertion_time
        ]
        inventory_to_add = inventory.Inventory()
        for txn in txns_to_add:
            for posting in txn.postings:
                inventory_to_add.add_position(posting)
        amount_to_add = inventory_to_add.get_currency_units(
            truelayer_balance['currency'])
        
        number = currency_to_decimal(truelayer_balance['current'])
        if account['liability']:
            number = -number
        number += amount_to_add.number
        number -= amount_to_remove.number
        return Balance(
            meta=new_metadata('', 0),
            date=assertion_time.date(),
            account=account['beancount_account'],
            amount=Amount(number, truelayer_balance['currency']),
            tolerance=None,
            diff_amount=None,
        )

    def _transform_transaction(
            self,
            truelayer_txn: dict[str, Any],
            beancount_account: str,
            is_pending: bool = False) -> Transaction:
        """Transforms TrueLayer Transaction to beancount Transaction."""

        number = abs(currency_to_decimal(truelayer_txn['amount']))
        if truelayer_txn['transaction_type'] == 'DEBIT':
            number = -number
        elif truelayer_txn['transaction_type'] == 'CREDIT':
            pass
        else:
            assert False

        posting = Posting(
            account=beancount_account,
            units=Amount(number, truelayer_txn['currency']),
            cost=None,
            price=None,
            flag=None,
            meta=None,
        )
        payee = (
            truelayer_txn.get('merchant_name', None) or
            truelayer_txn['meta'].get('provider_merchant_name', None))
        return Transaction(
            meta=new_metadata('', 0),
            date=dateutil.parser.parse(truelayer_txn['timestamp']).astimezone().date(),
            flag='!' if is_pending else '*',
            payee=payee,
            narration=truelayer_txn['description'],
            tags=set(),
            links=set(),
            postings=[posting],
        )


class _OAuthManager:
    ADDRESS = '127.0.0.1'
    PORT = 3000
    REDIRECT_URI = 'http://localhost:3000/callback'

    def __init__(self, config: _Config):
        self._config = config
    
    @property
    def access_token(self) -> str:
        access_token = self._get_valid_access_token()
        if access_token:
            return access_token
        self._refresh_access_token()
        access_token = self._get_valid_access_token()
        if access_token:
            return access_token
        self._request_access_token()
        access_token = self._get_valid_access_token()
        if access_token:
            return access_token
        raise RuntimeError('Unable to get a valid access token.')

    def _get_valid_access_token(self) -> Optional[str]:
        """Get access token from config file."""

        access_token = self._config.data.get('access_token')
        expiry_time = self._config.data.get('access_token_expiry_time')
        now = int(time.time())
        if access_token and expiry_time and expiry_time > now:
            return access_token
        return None

    def _refresh_access_token(self) -> None:
        """Refresh access token with refresh token."""

        logging.info('Attempt to refresh access token.')
        refresh_token = self._config.data.get('refresh_token', None)
        if not refresh_token:
            logging.info(
                'Failed to refresh access token: refresh token not available.')
            return
        self._grant_access_token(refresh_token=refresh_token)

    def _request_access_token(self) -> None:
        """Get access token with regular OAuth flow."""

        logging.info('Attempt to request access token with regular OAuth flow.')
        code = self._request_code()
        self._grant_access_token(code=code)
        logging.info('Successfully requested access token.')

    def _grant_access_token(self, code: Optional[str] = None, refresh_token: Optional[str] = None) -> None:
        """Grant access token with code or refresh_token."""

        logging.info('Attempt to grant access token.')
        req = {
            'client_id': self._config.client_id,
            'client_secret': self._config.client_secret,
        }
        if code:
            req['grant_type'] = 'authorization_code'
            req['redirect_uri'] = self.REDIRECT_URI
            req['code'] = code
        elif refresh_token:
            req['grant_type'] = 'refresh_token'
            req['refresh_token'] = refresh_token
        else:
            assert False
        r = requests.post('https://auth.truelayer.com/connect/token', req)
        if r.status_code != 200:
            logging.warning(
                f'Failed to grant access token: server returns '
                f'{r.status_code}')
            return
        data = r.json()
        self._config.data['access_token'] = data['access_token']
        self._config.data['access_token_expiry_time'] = (
            int(time.time()) + data['expires_in'])
        self._config.data['refresh_token'] = data['refresh_token']
        self._config.dump()
        logging.info('Successfully granted access token.')

    def _request_code(self) -> str:
        """Get the code to redeem access token with regular OAuth flow."""

        state = secrets.token_urlsafe(16)
        code = None
        auth_link = None

        class HttpHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                logging.info('OAuth response received.')
                length = int(self.headers['Content-Length'])
                body = self.rfile.read(length).decode('utf-8')
                data = dict(urllib.parse.parse_qsl(body))
                received_state = data.get('state')
                received_code = data.get('code')

                if received_code and received_state == state:
                    nonlocal code
                    code = received_code
                    self.send_response(200)
                    response = b'You can now close this tab.\n'
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Content-Length', str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
                else:
                    if received_state != state:
                        logging.warning('OAuth response state mismatches.')
                    elif not received_code:
                        logging.warning('OAuth response misses code.')
                    self.send_response(302)
                    assert auth_link
                    self.send_header('Location', auth_link)

        httpd = http.server.HTTPServer((self.ADDRESS, self.PORT), HttpHandler)
        socketname = httpd.socket.getsockname()
        logging.info(f'OAuth server listening at {socketname}')
        auth_link = self._build_auth_link(state)
        webbrowser.open_new(auth_link)

        print(
            f'Please navigate to the following URL to complete the '
            f'authorization process:\n\n'
            f'{auth_link}\n\n'
            f'If you are unable to visit the link on the same '
            f'host that this script is running on, you might need to '
            f'forward TCP port {socketname[1]} to the host where the '
            f'browser will be running on during the process.',
            file=sys.stderr)

        while not code:
            httpd.handle_request()
        httpd.server_close()
        return code

    def _build_auth_link(self, state: str) -> str:
        qs = urllib.parse.urlencode({
            'response_type': 'code',
            'response_mode': 'form_post',
            'client_id': self._config.client_id,
            'redirect_uri': self.REDIRECT_URI,
            'scope': ' '.join([
                'accounts',
                'cards',
                'transactions',
                'balance',
                'offline_access',
            ]),
            'state': state,
        })
        return f'https://auth.truelayer.com/?{qs}'

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'WARNING'))
