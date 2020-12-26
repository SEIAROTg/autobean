import datetime
from decimal import Decimal
import http.server
import json
import logging
import os
import re
import time
import secrets
import sys
from typing import Text
import urllib.parse
import webbrowser

from beancount.core.amount import Amount
from beancount.core.data import Transaction, Posting, new_metadata
from beancount.ingest import importer
import dateutil.parser
import requests
import yaml


CONFIG_SUFFIX = '.truelayer.yaml'
ACCOUNT_TYPES = ('accounts', 'cards')


def escape_account_component(s):
    s = re.sub(r'\W', '', s)
    s = s[:1].upper() + s[1:]
    return s


def format_iso_datetime(timestamp_s):
    return datetime.datetime.utcfromtimestamp(int(timestamp_s)).isoformat()


class Importer(importer.ImporterProtocol):

    def __init__(self, client_id: Text, client_secret: Text):
        self._client_id = client_id
        self._client_secret = client_secret

    def name(self):
        return 'autobean.truelayer'

    def identify(self, file):
        return file.name.endswith(CONFIG_SUFFIX)

    def extract(self, file, existing_entries=None):
        config = _Config(self._client_id, self._client_secret, file)
        extractor = _Extractor(config)
        return extractor.extract(existing_entries)


class _Config:
    def __init__(self, client_id, client_secret, file):
        self.client_id = client_id
        self.client_secret = client_secret
        self.data = yaml.safe_load(file.contents()) or {}
        self._filename = file.name

    @property
    def name(self):
        return os.path.basename(self._filename).rsplit(CONFIG_SUFFIX, 1)[0]

    def dump(self):
        with open(self._filename, 'w') as f:
            yaml.safe_dump(self.data, f)


class _Extractor:
    def __init__(self, config: _Config):
        self._config = config
        self._oauth_manager = _OAuthManager(config)

    def extract(self, existing_entries=None):
        for type_ in ACCOUNT_TYPES:
            self._update_accounts(type_)
        entries = self._fetch_all_transactions()
        # TODO: dedup
        return entries

    @property
    def _auth_headers(self):
        return {
            'Authorization': f'Bearer {self._oauth_manager.access_token}'
        }

    def _update_accounts(self, type_: Text):
        url = {
            'accounts': 'https://api.truelayer.com/data/v1/accounts',
            'cards': 'https://api.truelayer.com/data/v1/cards',
        }
        r = requests.get(url[type_], headers=self._auth_headers)
        accounts = r.json().get('results', [])
        config_accounts = self._config.data.setdefault(type_, {})
        for account in accounts:
            config_account = config_accounts.setdefault(
                account['account_id'], {})
            config_account.setdefault('name', account['display_name'])
            config_account.setdefault(
                'liability',
                type_ == 'card' and account['card_type'] == 'CREDIT')
            config_account.setdefault('enabled', True)
            config_account.setdefault('beancount_account', ':'.join([
                'Liabilities' if config_account['liability'] else 'Assets',
                escape_account_component(self._config.name),
                escape_account_component(config_account['name'])
            ]))
            config_account.setdefault('from', time.time() - 86400 * 90)

        self._config.dump()

    def _fetch_transactions(
            self,
            account_id: Text,
            account,
            type_: Text,
            is_pending: bool):
        url = {
            ('accounts', False): (
                'https://api.truelayer.com/data/v1/accounts/{account_id}/transactions'),
            ('accounts', True): (
                'https://api.truelayer.com/data/v1/accounts/{account_id}/transactions/pending'),
            ('cards', False): (
                'https://api.truelayer.com/data/v1/cards/{account_id}/transactions'),
            ('cards', True): (
                'https://api.truelayer.com/data/v1/cards/{account_id}/transactions/pending'),
        }
        log_transaction = 'pending transactions' if is_pending else 'transactions'
        logging.info(
            f'Fetching {log_transaction} for account {account["name"]} '
            f'({account_id}).')
        r = requests.get(
            url[(type_, is_pending)].format(account_id=account_id),
            headers=self._auth_headers,
            params={
                'from': format_iso_datetime(account['from']),
                'to': format_iso_datetime(time.time()),
            }
        )
        txns = r.json().get('results', [])
        logging.info(
            f'Fetched {len(txns)} {log_transaction} for account '
            f'{account["name"]} ({account_id}).')
        return txns

    def _fetch_all_transactions(self):
        entries = []
        for type_ in ACCOUNT_TYPES:
            for account_id, account in self._config.data[type_].items():
                if not account['enabled']:
                    continue
                truelayer_txns = []
                for is_pending in (False, True):
                    truelayer_txns.extend(self._fetch_transactions(
                        account_id,
                        account,
                        type_,
                        is_pending))
                txns = [
                    self._transform_transaction(
                        truelayer_txn, account['beancount_account'])
                    for truelayer_txn in truelayer_txns
                ]
                # produce balance
                entries.extend(txns)
        return entries

    def _transform_transaction(
            self,
            truelayer_txn,
            beancount_account: Text,
            is_pending: bool=False):
        """Transforms TrueLayer Transaction to beancount Transaction."""

        amount = abs(Decimal(str(truelayer_txn['amount'])))
        if truelayer_txn['transaction_type'] == 'DEBIT':
            amount = -amount
        elif truelayer_txn['transaction_type'] == 'CREDIT':
            pass
        else:
            assert False

        posting = Posting(
            account=beancount_account,
            units=Amount(amount, truelayer_txn['currency']),
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
            date=dateutil.parser.parse(truelayer_txn['timestamp']).date(),
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
    def access_token(self):
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

    def _get_valid_access_token(self):
        """Get access token from config file."""

        access_token = self._config.data.get('access_token')
        expiry_time = self._config.data.get('access_token_expiry_time')
        now = int(time.time())
        if access_token and expiry_time and expiry_time > now:
            return access_token

    def _refresh_access_token(self):
        """Refresh access token with refresh token."""

        logging.info('Attempt to refresh access token.')
        refresh_token = self._config.data.get('refresh_token', None)
        if not refresh_token:
            logging.info(
                'Failed to refresh access token: refresh token not available.')
            return
        self._grant_access_token(refresh_token=refresh_token)

    def _request_access_token(self):
        """Get access token with regular OAuth flow."""

        logging.info('Attempt to request access token with regular OAuth flow.')
        code = self._request_code()
        access_token = self._grant_access_token(code=code)
        logging.info('Successfully requested access token.')

    def _grant_access_token(self, code=None, refresh_token=None):
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
            req['grant_type'] = 'refresh_token',
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

    def _request_code(self):
        """Get the code to redeem access token with regular OAuth flow."""

        state = secrets.token_urlsafe(16)
        code = None
        auth_link = None

        class HttpHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                logging.info('OAuth response received.')
                length = int(self.headers.get('Content-Length'))
                body = self.rfile.read(length).decode('utf-8')
                data = urllib.parse.parse_qs(body)
                received_state = data.get('state', [None])[0]
                received_code = data.get('code', [None])[0]

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

    def _build_auth_link(self, state):
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