from urllib.parse import unquote_plus
import websocket
import requests
import json

from pymeritrade.stream import TDAStream
from pymeritrade.errors import TDAPermissionsError


class TDAClient:

    def __init__(self, consumer_key, open_browser=True, redirect_uri='http://localhost', account_idx=0):
        self.consumer_key = consumer_key
        self.redirect_uri = redirect_uri
        self.open_browser = open_browser
        self.account_idx = account_idx
        self.account_id = None
        self.access_token = None
        self.refresh_token = None
        self.last_creds_fn = None

    def _call_api(self, path, params=None, method='GET'):
        kwargs = {}
        kwargs['headers'] = {'Authorization': 'Bearer ' + self.access_token}
        if params is not None:
            kwargs['params'] = params
        resp = requests.get('https://api.tdameritrade.com/v1/' + path, **kwargs)
        return resp.json()

    def login(self, regen_on_failed_refresh=True):
        if self.access_token is None:
            print('Generating access token...')
            self._manual_token_gen()
        if not self._check_login() and not self._refresh_token():
            if regen_on_failed_refresh:
                self.access_token = None
                self.refresh_token = None
                self.login(regen_on_failed_refresh=False)
            else:
                raise TDAPermissionsError('Login failed')
        else:
            self._setup()

    def _manual_token_gen(self):
        auth_url = ('https://auth.tdameritrade.com/auth?' + 
            'response_type=code&redirect_uri={}&client_id={}@AMER.OAUTHAP'.format(self.redirect_uri, self.consumer_key))
        print('Go to the link below, login, then copy the code from the url.')
        print(auth_url)
        if self.open_browser:
            import webbrowser
            webbrowser.open(auth_url)
        code = unquote_plus(input('code > '))
        resp = self._call_oauth(dict(
            grant_type='authorization_code', 
            access_type='offline', 
            client_id=self.consumer_key + '@AMER.OAUTHAP', 
            redirect_uri=self.redirect_uri, 
            code=code
        ))
        try:
            self.access_token = resp['access_token']
            self.refresh_token = resp['refresh_token']
        except KeyError:
            raise TDAPermissionsError('Login failed ' + str(resp))

    def _refresh_token(self):
        resp = self._call_oauth(dict(
            grant_type='refresh_token', 
            access_type='offline', 
            client_id=self.consumer_key + '@AMER.OAUTHAP', 
            refresh_token=self.refresh_token
        ))
        if 'access_token' in self.access_token:
            self.access_token = resp['access_token']
            return True
        return False

    def _call_oauth(self, params):
        resp = requests.post('https://api.tdameritrade.com/v1/oauth2/token', data=params).json()
        return resp

    def _check_login(self):
        return 'error' not in self.principles

    def _setup(self):
        self.account_id = self.accounts[self.account_idx]['securitiesAccount']['accountId']
        if self.last_creds_fn is not None:
            self.save_login(fn=self.last_creds_fn)

    def save_login(self, fn='tda-login'):
        self.last_creds_fn = fn
        with open(fn, 'w') as lf:
            json.dump(dict(access_token=self.access_token, refresh_token=self.refresh_token), lf)

    def load_login(self, fn='tda-login'):
        self.last_creds_fn = fn
        with open(fn, 'r') as lf:
            creds = json.load(lf)
        self.access_token = creds['access_token']
        self.refresh_token = creds['refresh_token']
        self.login()

    @property
    def principles(self):
        return self._call_api('userprincipals', params=dict(fields='streamerSubscriptionKeys,streamerConnectionInfo'))

    @property
    def accounts(self):
        return self._call_api('accounts')

    @property
    def account(self):
        return self._call_api('accounts/{}'.format(self.account_id))['securitiesAccount']

    @property
    def equity(self):
        return self.account['currentBalances']['equity']

    @property
    def day_trades(self):
        return self.account['roundTrips']

    @property
    def buying_power(self):
        return self.account['currentBalances']['buyingPower']

    @property
    def liquidation_value(self):
        return self.account['currentBalances']['liquidationValue']

    def create_stream(self, **kwargs):
        return TDAStream(self, **kwargs)