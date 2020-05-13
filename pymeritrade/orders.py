from datetime import datetime

from pymeritrade.errors import TDAAPIError


JSON_KEYS = {
    'session': 'session',
    'duration': 'duration',
    'orderType': 'order_type',
    'quantity': 'quantity',
    'price': 'price',
    'complexOrderStrategyType': 'complex_strat_type',
    'orderStrategyType': 'strat_type',
    'status': 'status',
    'requestedDestination': 'req_dest',
    'destinationLinkName': 'dest_link_name',
    'orderLegCollection': 'actions',
    'tag': 'tag',
    'cancelable': 'cancelable',
    'editable': 'editable'
}


class TDAOrder:

    def __init__(self, client, _id, raw_json, **kwargs):
        self.client = client
        self._id = _id
        self.raw_json = raw_json

    @staticmethod
    def from_new(client, **kwargs):
        return TDAOrder(client, None, None)
    
    @staticmethod
    def from_json(client, json_data):
        kwargs = {}
        for json_key, kwarg in JSON_KEYS.items():
            kwargs[kwarg] = json_data[json_key]
        return TDAOrder(client, json_data['orderId'], json_data, **kwargs)

    def _post_order(self, symbols):
        resp = self.client._call_api(
            'accounts/{}/orders'.format(self.client.account_id), 
            method='POST'
        )
        return resp

    def exec(self):
        # TODO
        assert False


class TDAOrders:

    def __init__(self, client):
        self.client = client

    def _get_orders(self, start, end, max_results=100):
        resp = self.client._call_api('orders', params={
            'accountId': self.client.account_id,
            'maxResults': max_results,
            'fromEnteredTime': start.strftime('%Y-%m-%d'),
            'toEnteredTime': end.strftime('%Y-%m-%d')
        })
        items = [TDAOrder.from_json(self.client, data) for data in resp]
        return items

    def all(self):
        start = datetime(1971, 1, 1)
        end = datetime.now()
        return self._get_orders(start, end)