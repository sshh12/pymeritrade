import pandas as pd

from pymeritrade.errors import TDAAPIError
from pymeritrade.utils import *


class TDAOptions:
    def __init__(self, client, **kwargs):
        self.client = client
        self.parse_dates = kwargs.get("parse_dates", True)
        self.range = kwargs.get("range")
        self.contracts = kwargs.get("contracts", "all")
        self.quotes = kwargs.get("quotes", True)
        self.strategy = kwargs.get("strategy", "single")
        self.strike = kwargs.get("strike")
        self.exp_month = kwargs.get("exp_month", "all")

    def _query_options(self, symbol):
        params = dict(
            symbol=symbol,
            contractType=self.contracts.upper(),
            includeQuotes=str(self.quotes).upper(),
            strategy=self.strategy.upper(),
            expMonth=self.exp_month.upper(),
        )
        if self.strike is not None:
            params["strike"] = self.strike
        if self.range is not None:
            params["strikeCount"] = self.range
        resp = self.client._call_api("marketdata/chains".format(symbol), params=params)
        options_all = []
        for key in ["callExpDateMap", "putExpDateMap"]:
            for exp, strikes in resp.get(key, {}).items():
                for strike, options in strikes.items():
                    options_all.extend(options)
        df = pd.DataFrame(options_all)
        df = clean_col_names(df)
        df["stock_symbol"] = symbol
        df["interest_rate"] = resp["interestRate"]
        df["overall_volatility"] = resp["volatility"]
        df["overall_strategy"] = resp["strategy"]
        df["vol_by_oi"] = df["total_volume"] / df["open_interest"]
        if self.parse_dates:
            df = parse_date_cols(df, ["expiration_date", "trade_time", "quote_time", "last_trading_day"])
        df = df.set_index("symbol")
        return df

    def __getitem__(self, key):
        return self._query_options(key)
