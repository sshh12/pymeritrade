import requests
import json

from pymeritrade.stream.stream import TDAStream
from pymeritrade.history import TDAHistory
from pymeritrade.options import TDAOptions
from pymeritrade.quotes import TDAQuotes
from pymeritrade.orders import TDAOrder, TDAOrders
from pymeritrade.instruments import TDAInstruments
from pymeritrade.errors import TDAPermissionsError
from pymeritrade.auth import DefaultAuthHandler


class TDAClient:
    def __init__(self, consumer_key, auth_handler=DefaultAuthHandler, redirect_uri="http://localhost", account_idx=0):
        self.consumer_key = consumer_key
        self.redirect_uri = redirect_uri
        self.account_idx = account_idx
        self.account_id = None
        self.access_token = None
        self.refresh_token = None
        self.last_creds_fn = None
        self.auth_handler = auth_handler(self)

    def _call_api(self, path, params=None, method="GET"):
        kwargs = {}
        kwargs["headers"] = {"Authorization": "Bearer " + self.access_token}
        if params is not None:
            kwargs["params"] = params
        resp = requests.get("https://api.tdameritrade.com/v1/" + path, **kwargs)
        try:
            return resp.json()
        except json.decoder.JSONDecodeError:
            return {"error": "parse error", "content": resp.text}

    def login(self):
        self.auth_handler.login()

    def _refresh_token(self):
        resp = self._call_oauth(
            dict(
                grant_type="refresh_token",
                access_type="offline",
                client_id=self.consumer_key + "@AMER.OAUTHAP",
                refresh_token=self.refresh_token,
            )
        )
        if "access_token" not in resp:
            return False
        self.access_token = resp["access_token"]
        return True

    def _call_oauth(self, params):
        return requests.post("https://api.tdameritrade.com/v1/oauth2/token", data=params).json()

    def check_login(self):
        return "error" not in self.principles

    def _setup(self):
        self.account_id = self.accounts[self.account_idx]["securitiesAccount"]["accountId"]
        if self.last_creds_fn is not None:
            self.save_login(fn=self.last_creds_fn)

    def save_login(self, fn="tda-login"):
        self.last_creds_fn = fn
        with open(fn, "w") as lf:
            json.dump(dict(access_token=self.access_token, refresh_token=self.refresh_token), lf)

    def load_login(self, fn="tda-login"):
        self.last_creds_fn = fn
        try:
            with open(fn, "r") as lf:
                creds = json.load(lf)
            self.access_token = creds["access_token"]
            self.refresh_token = creds["refresh_token"]
        except FileNotFoundError:
            print("Login not found...skipping load.")
        self.login()

    @property
    def principles(self):
        return self._call_api("userprincipals", params=dict(fields="streamerSubscriptionKeys,streamerConnectionInfo"))

    @property
    def accounts(self):
        return self._call_api("accounts")

    @property
    def account(self):
        return self._call_api("accounts/{}".format(self.account_id))["securitiesAccount"]

    @property
    def equity(self):
        return self.account["currentBalances"]["equity"]

    @property
    def day_trades(self):
        return self.account["roundTrips"]

    @property
    def buying_power(self):
        return self.account["currentBalances"]["buyingPower"]

    @property
    def liquidation_value(self):
        return self.account["currentBalances"]["liquidationValue"]

    @property
    def orders(self):
        return TDAOrders(self)

    @property
    def instruments(self):
        return TDAInstruments(self)

    @property
    def stocks(self):
        return self.instruments

    def create_stream(self, **kwargs):
        return TDAStream(self, **kwargs)

    def movers(self, index="$DJI", direction=None):
        params = {}
        if direction:
            params["direction"] = direction.lower()
        return self._call_api("marketdata/{}/movers".format(index), params=params)

    def history(self, **kwargs):
        return TDAHistory(self, **kwargs)

    def options(self, **kwargs):
        return TDAOptions(self, **kwargs)

    def quotes(self, **kwargs):
        return TDAQuotes(self, **kwargs)
