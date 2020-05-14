from pymeritrade.errors import TDAAPIError


class TDAQuotes:

    def __init__(self, client, **kwargs):
        self.client = client

    def _call_api(self, symbols):
        resp = self.client._call_api('marketdata/quotes', params={'symbol': ','.join(symbols)})
        return resp

    def __getitem__(self, key):
        if type(key) == str:
            return self._call_api([key])[key]
        return self._call_api(key)