from urllib.parse import urlencode
from datetime import datetime
import websocket
import time
import json


class TDAStream:

    def __init__(self, client):
        self.principles = client.principles
        self.ws_uri = 'wss://' + self.principles['streamerInfo']['streamerSocketUrl'] + '/ws'
        self.token_ts = iso_to_ms(self.principles['streamerInfo']['tokenTimestamp'])
        self.acc_id = self.principles['accounts'][0]['accountId']
        self.app_id = self.principles['streamerInfo']['appId']

        self.cmd_buffer = []
        self.req_id_cnt = 0
        self.ws = None
        self.ws_started = False
        self.ws_ready = False

    def _cmd(self, service, command, params, id_=None, send=True):
        if id_ is None:
            self.req_id_cnt += 1
            id_ = self.req_id_cnt
        for key, val in params.items():
            if type(val) == list:
                params[key] = ','.join([str(v) for v in val])
        self.cmd_buffer.append({
            'service': service.upper(),
            'command': command.upper(),
            'requestid': str(id_),
            'account': self.acc_id,
            'source': self.app_id,
            'parameters': params
        })
        if send:
            reqs = {
                'requests': self.cmd_buffer
            }
            self.ws.send(json.dumps(reqs))

    def _on_ws_open(self, ws):
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
        self.ws = ws
        self._cmd('admin', 'login', login_params, id_='login')

    def _on_ws_msg(self, msg):
        msg_json = json.loads(msg)
        print(msg_json)
        for resp in msg_json.get('response', []):
            if resp['requestid'] == 'login':
                self.ws_ready = True
        for data in msg_json.get('data', []):
            print(data['content'])

    def _on_ws_error(self, err):
        pass

    def _on_ws_close(self):
        pass

    def start(self):
        ws = websocket.WebSocketApp(self.ws_uri, 
            on_message=lambda msg: self._on_ws_msg(msg), 
            on_error=lambda err: self._on_ws_error(err), 
            on_close=lambda ws: self._on_ws_close(), 
            on_open=lambda ws: self._on_ws_open(ws))
        self.ws_started = True
        ws.run_forever()


def iso_to_ms(iso_date):
    date = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S%z")
    return int(date.timestamp() * 1000)