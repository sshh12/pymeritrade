from pymeritrade.errors import TDAAPIError


class TDAQuotes:
    def __init__(self, client, **kwargs):
        self.client = client

    def _query_quotes(self, symbols):
        return self.client._call_api("marketdata/quotes", params={"symbol": ",".join(symbols)})

    def __getitem__(self, key):
        if type(key) == str:
            return self._query_quotes([key])[key]
        return self._query_quotes(key)
