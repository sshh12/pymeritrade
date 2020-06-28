from datetime import datetime


class TDAOrder:
    def __init__(self, client, json_data):
        self.client = client
        self.json = json_data
        self.id = self.json["orderId"]
        self.session = self.json.get("session", "normal")
        self.duration = self.json.get("duration", "day")
        self.order_type = self.json.get("order_type", "market")
        self.complex_strat_type = self.json.get("complex_strat_type", "none")

    @staticmethod
    def from_new(client, **kwargs):
        return TDAOrder(client, None, {}, **kwargs)

    @staticmethod
    def from_json(client, json_data):
        return TDAOrder(client, json_data)

    def __repr__(self):
        return f"<Order ({self.id})>"

    def _post_order(self, symbols):
        resp = self.client._call_api("accounts/{}/orders".format(self.client.account_id), method="POST")
        return resp

    def exec(self):
        params = {"session": self.session, "duration": self.duration, "orderType": self.order_type}
        print(params)


class TDAOrders:
    def __init__(self, client):
        self.client = client

    def _get_orders(self, start, end, max_results=100):
        resp = self.client._call_api(
            "orders",
            params={
                "accountId": self.client.account_id,
                "maxResults": max_results,
                "fromEnteredTime": start.strftime("%Y-%m-%d"),
                "toEnteredTime": end.strftime("%Y-%m-%d"),
            },
        )
        items = [TDAOrder.from_json(self.client, data) for data in resp]
        return items

    def all(self):
        start = datetime(1971, 1, 1)
        end = datetime.now()
        return self._get_orders(start, end)
