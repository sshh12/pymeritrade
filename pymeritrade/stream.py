from urllib.parse import urlencode
from collections import defaultdict
from datetime import datetime
import threading
import websocket
import queue
import time
import json

from pymeritrade.errors import TDAPermissionsError, check_assert


SUB_TYPES = {
    'news': ('NEWS_HEADLINE', 'SUBS', 'NEWS_HEADLINE-SUBS', [0, 3, 4, 5, 8], {}),
    'newslist': ('NEWS_HEADLINELIST', 'SUBS', 'NEWS_HEADLINELIST-SUBS', [0, 1], {}),
    'forex': ('LEVELONE_FOREX', 'SUBS', 'LEVELONE_FOREX-SUBS', [0, 1, 2, 3, 4, 5, 6], {}),
    'quote': ('QUOTE', 'SUBS', 'QUOTE-SUBS', [0, 1, 2, 3, 8], {}),
    'chart': ('CHART_type', 'SUBS', 'CHART_type-SUBS', [0, 1, 2, 3, 4, 5, 6, 7, 8], 
        {'type': {'equity': 'EQUITY', 'futures': 'FUTURES', 'options': 'OPTIONS'}}),
    'actives': ('ACTIVES_exchange', 'SUBS', 'ACTIVES_exchange-SUBS', [0, 1], 
        {'exchange': {'NASDAQ': 'NASDAQ', 'NYSE': 'NYSE', 'OPTIONS': 'OPTIONS', 'OTCBB': 'OTCBB'}}),
}
SUB_ID_TO_NAME = {val[2]: key for key, val in SUB_TYPES.items()}


class TDAStream:

    def __init__(self, client, debug=False):
        self.principles = client.principles
        self.ws_uri = 'wss://' + self.principles['streamerInfo']['streamerSocketUrl'] + '/ws'
        self.token_ts = _iso_to_ms(self.principles['streamerInfo']['tokenTimestamp'])
        self.acc_id = self.principles['accounts'][0]['accountId']
        self.app_id = self.principles['streamerInfo']['appId']
        self.debug = debug

        self.cmd_buffer = []
        self.req_id_cnt = 0
        self.ws = None
        self.ws_started = False
        self.ws_ready = False
        self.thread = None
        self.data_qs = defaultdict(lambda: None)

    def _log(self, *args):
        if self.debug:
            print(*args)

    def _cmd(self, service, command, params={}, id_=None, send=True):
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
            self.cmd_buffer = []
            self._log('SENT', reqs)
        return id_

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
        for resp in msg_json.get('response', []):
            self._on_resp(resp)
        for note in msg_json.get('notify', []):
            self._on_notify(note)
        for data in msg_json.get('data', []):
            self._on_data(data)

    def _on_ws_error(self, err):
        self._log('ERROR', err)

    def _on_ws_close(self):
        self._log('CLOSED')

    def _on_resp(self, resp):
        self._log('RESP', resp)
        if resp['requestid'] == 'login':
            self.ws_ready = True

    def _on_notify(self, info):
        self._log('NOTIFY', info)

    def _on_data(self, data):
        key = _msg_to_key(data)
        name = SUB_ID_TO_NAME[key]
        self._log('DATA', key, data)
        def _append_data(q):
            if q is not None:
                q.put((name, data['content']))
        _append_data(self.data_qs[key])
        _append_data(self.data_qs['*'])

    def start(self):
        ws = websocket.WebSocketApp(self.ws_uri, 
            on_message=lambda ws, msg: self._on_ws_msg(msg), 
            on_error=lambda err: self._on_ws_error(err), 
            on_close=lambda ws: self._on_ws_close(), 
            on_open=lambda ws: self._on_ws_open(ws))
        self.ws_started = True
        self.thread = threading.Thread(target=ws.run_forever)
        self.thread.start()
        while not self.ws_ready:
            time.sleep(0.1)

    def subscribe(self, name, **params):
        check_assert(self.ws_ready, 'Websocket not ready')
        check_assert(name in SUB_TYPES)
        check_assert(len(params['symbols']) > 0, 'At least one symbol needed.')
        service, cmd, id_, default_fields, mods = SUB_TYPES[name]
        for mod, translation in mods.items():
            selected = translation.get(params.get(mod))
            check_assert(selected is not None, mod + ' not provided')
            service = service.replace(mod, selected)
            id_ = id_.replace(mod, selected)
        self._cmd(service, cmd, {'keys': params.get('symbols', ''), 'fields': params.get('fields', default_fields)})
        return self._make_queue_iter('news', id_)

    def live_data(self):
        return self._make_queue_iter('*', '*')()

    def _make_queue_iter(self, clean_name, name):
        data_q = self.data_qs[name]
        if data_q is None:
            data_q = queue.Queue()
            self.data_qs[name] = data_q
        def data_iter():
            while True:
                type_name, items = data_q.get(block=True)
                item_dict = {val['key']: val for val in items}
                yield type_name, item_dict
        return data_iter

    def logout(self):
        check_assert(self.ws_ready, 'Websocket not ready')
        self._cmd('admin', 'logout')


def _iso_to_ms(iso_date):
    date = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%S%z")
    return int(date.timestamp() * 1000)


def _msg_to_key(msg):
    return '{}-{}'.format(msg['service'], msg['command'])