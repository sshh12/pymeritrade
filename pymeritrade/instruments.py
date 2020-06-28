from pymeritrade.errors import TDAAPIError


class TDAInstrument:
    def __init__(self, client, json_data):
        self.client = client
        self.json = json_data
        self.symbol = self.json["symbol"]
        self.cusip = self.json["symbol"]
        self.desc = self.json["description"]
        self.exhange = self.json["exchange"]
        self.asset_type = self.json["assetType"]

    @staticmethod
    def from_json(client, json_data):
        return TDAInstrument(client, json_data)

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
        return "<Instrument [{}]>".format(self.symbol)


class TDAInstruments:

    CACHE = {}

    def __init__(self, client):
        self.client = client

    def _query_instruments(self, query, search):
        return self.client._call_api("instruments", params={"symbol": query, "projection": search})

    def fundamentals(self, query):
        return self._query_instruments(query, "fundamental")[query]["fundamental"]

    def __getitem__(self, symbol):
        if symbol in TDAInstruments.CACHE:
            return TDAInstruments.CACHE[symbol]
        data = self._query_instruments(symbol, "symbol-search")
        if symbol in data:
            return TDAInstrument.from_json(self.client, data[symbol])
        raise TDAAPIError(f"{symbol} not found.")
