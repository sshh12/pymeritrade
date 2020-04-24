from urllib.parse import urlencode, unquote_plus
import websocket
import requests
import time
import json


class TDClient:

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

    def _manual_token_gen(self):
        auth_url = ('https://auth.tdameritrade.com/auth?' + 
            'response_type=code&redirect_uri={}&client_id={}@AMER.OAUTHAP'.format(self.redirect_uri, self.consumer_key))
        print(auth_url)
        code = unquote_plus(input('code > '))
        resp = self._call_oauth(dict(
            grant_type='authorization_code', 
            access_type='offline', 
            client_id=self.consumer_key + '@AMER.OAUTHAP', 
            redirect_uri=self.redirect_uri, 
            code=code
        ))
        print(resp)
        self.access_token = resp['access_token']
        self.refresh_token = resp['refresh_token']

    def _refresh_token(self):
        resp = _call_oauth(dict(
            grant_type='refresh_token', 
            access_type='offline', 
            client_id=self.consumer_key + '@AMER.OAUTHAP', 
            refresh_token=self.refresh_token
        ))
        self.access_token = resp['access_token']

    def _call_oauth(self, params):
        print(params)
        resp = requests.post('https://api.tdameritrade.com/v1/oauth2/token', data=params).json()
        return resp

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

    def stream(self):
        principles = self.get_user_principles()
        stream = TDAStream(principles)
        return stream


class TDAStream:

    def __init__(self, principles):
        self.principles = principles
        self.ws_uri = 'wss://' + principles['streamerInfo']['streamerSocketUrl'] + '/ws'
        self.token_ts = int(pendulum.parse(principles['streamerInfo']['tokenTimestamp']).float_timestamp * 1000)
        self.acc_id = principles['accounts'][0]['accountId']
        self.app_id = principles['streamerInfo']['appId']
        self.req_id_cnt = 0
        self.ws = None
        self.logged_in = False

    def cmd(self, service, command, params, id_=None):
        if id_ is None:
            self.req_id_cnt += 1
            id_ = self.req_id_cnt
        for key, val in params.items():
            if type(val) == list:
                params[key] = ','.join([str(v) for v in val])
        reqs = {
            'requests': [
                {
                    'service': service.upper(),
                    'command': command.upper(),
                    'requestid': str(id_),
                    'account': self.acc_id,
                    'source': self.app_id,
                    'parameters': params
                }
            ]
        }
        print('SENDING', reqs)
        self.ws.send(json.dumps(reqs))

    def start(self):
        creds = {
            'userid': self.acc_id,
            'token': self.principles['streamerInfo']['token'],
            'company': self.principles['accounts'][0]['company'],
            'segment': self.principles['accounts'][0]['segment'],
            'cddomain': self.principles['accounts'][0]['accountCdDomainId'],
            'usergroup': self.principles['streamerInfo']['userGroup'],
            'accesslevel': self.principles['streamerInfo']['accessLevel'],
            'authorized': 'Y',
            'timestamp': self.token_ts,
            'appid': self.app_id,
            'acl': self.principles['streamerInfo']['acl']
        }
        login_params = {
            'credential': urlencode(creds),
            'token': self.principles['streamerInfo']['token'],
            'version': '1.0'
        }
        def on_message(ws, msg):
            msg_json = json.loads(msg)
            print(msg_json)
            for resp in msg_json.get('response', []):
                if resp['requestid'] == 'login':
                    self.logged_in = True
                print('RECV', resp)
            for data in msg_json.get('data', []):
                print(data['content'])
        def on_error(ws, error):
            print(error)
        def on_close(ws):
            print('CLOSED!')
        def on_open(ws):
            self.ws = ws
            self.cmd('admin', 'login', login_params, id_='login')
        ws = websocket.WebSocketApp(self.ws_uri, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open)
        thread.start_new_thread(ws.run_forever, ())
        while not self.logged_in:
            time.sleep(0.1)