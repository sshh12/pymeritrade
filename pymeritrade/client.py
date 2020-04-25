from urllib.parse import unquote_plus
import websocket
import requests
import json

from pymeritrade.stream import TDAStream
from pymeritrade.error import TDAPermissionsError


class TDAClient:

    def __init__(self, consumer_key, redirect_uri='http://localhost'):
        self.consumer_key = consumer_key
        self.redirect_uri = redirect_uri
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

    def login(self):
        if self.access_token is None:
            print('Generating access token...')
            self._manual_token_gen()
        if not self._check_login():
            self._refresh_token()
        if not self._check_login():
            raise TDAPermissionsError('Login failed')

    def _manual_token_gen(self):
        auth_url = ('https://auth.tdameritrade.com/auth?' + 
            'response_type=code&redirect_uri={}&client_id={}@AMER.OAUTHAP'.format(self.redirect_uri, self.consumer_key))
        print('Go to the link below, login, then copy the code from the url.')
        print(auth_url)
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
        self.access_token = resp['access_token']
        if self.last_creds_fn is not None:
            self.save_login(fn=self.last_creds_fn)

    def _call_oauth(self, params):
        resp = requests.post('https://api.tdameritrade.com/v1/oauth2/token', data=params).json()
        return resp

    def _check_login(self):
        return 'error' not in self.principles

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

    def create_stream(self, **kwargs):
        return TDAStream(self, **kwargs)