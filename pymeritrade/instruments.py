from pymeritrade.errors import TDAAPIError


class TDAInstruments:

    def __init__(self, client):
        self.client = client

    def _call_api(self, query, search):
        resp = self.client._call_api('instruments', params={
            'symbol': query,
            'projection': search
        })
        return resp

    def __getitem__(self, key):
        return self._call_api(key, 'symbol-search')