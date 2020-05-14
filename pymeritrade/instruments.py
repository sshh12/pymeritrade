from pymeritrade.errors import TDAAPIError


class TDAInstrument:

    def __init__(self, client, symbol, cusip, asset_type, exchange, desc=""):
        self.client = client
        self.symbol = symbol
        self.cusip = cusip
        self.desc = desc
        self.exhange = exchange
        self.asset_type = asset_type

    @staticmethod
    def from_json(client, json_data):
        symbol = json_data['symbol']
        return TDAInstrument(client, symbol, 
            json_data['cusip'], json_data['assetType'], 
            json_data['exchange'], desc=json_data['description'])

    @property
    def quote(self):
        return self.client.quotes()[self.symbol]

    @property
    def fundamentals(self):
        return self.client.instruments.fundamentals(self.symbol)

    def history(self, **kwargs):
        return self.client.history(**kwargs)[self.symbol]

    def options(self, **kwargs):
        return self.client.options(**kwargs)[self.symbol]

    def __repr__(self):
        return '<Instrument [{}]>'.format(self.symbol)


class TDAInstruments:

    CACHE = {}

    def __init__(self, client):
        self.client = client

    def _call_api(self, query, search):
        resp = self.client._call_api('instruments', params={
            'symbol': query,
            'projection': search
        })
        return resp

    def fundamentals(self, query):
        return self._call_api(query, 'fundamental')[query]['fundamental']

    def __getitem__(self, key):
        if key in TDAInstruments.CACHE:
            return TDAInstruments.CACHE[key]
        data = self._call_api(key, 'symbol-search')
        if key in data:
            return TDAInstrument.from_json(self.client, data[key])
        return None