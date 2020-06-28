from datetime import datetime
import pandas as pd

from pymeritrade.errors import TDAAPIError
from pymeritrade.utils import parse_date_cols


class TDAHistory:
    def __init__(self, client, **kwargs):
        self.client = client
        self.parse_dates = kwargs.get("parse_dates", True)
        if kwargs.get("span") == "all":
            kwargs["span"] = "year"
            kwargs["start"] = datetime(1970, 1, 2)
        if kwargs.get("latest"):
            kwargs["end"] = datetime.now()
        self.span = kwargs.get("span", "year")
        self.freq = kwargs.get("freq", "daily")
        self.extended = kwargs.get("extended", True)
        self.start = kwargs.get("start")
        self.end = kwargs.get("end")

    def _call_api(self, symbol):
        params = dict(periodType=self.span, frequencyType=self.freq, needExtendedHoursData=str(self.extended).lower())
        if self.start is not None:
            params["startDate"] = _date_to_ms(self.start)
        if self.end is not None:
            params["endDate"] = _date_to_ms(self.end)
        resp = self.client._call_api("marketdata/{}/pricehistory".format(symbol), params=params)
        if "candles" not in resp:
            raise TDAAPIError(resp["error"])
        df = pd.DataFrame(resp["candles"])
        if self.parse_dates:
            df = parse_date_cols(df, ["datetime"])
        df = df.set_index("datetime")
        return df

    def __getitem__(self, key):
        df = None
        if type(key) == str:
            df = self._call_api(key)
        elif type(key) == list:
            for symbol in key:
                sym_df = self._call_api(symbol)
                col_map = {c: symbol + "_" + c for c in sym_df.columns}
                sym_df = sym_df.rename(columns=col_map)
                if df is None:
                    df = sym_df
                else:
                    df = df.merge(sym_df, how="outer", left_index=True, right_index=True)
        return df


def _date_to_ms(date_or_ts):
    if type(date_or_ts) == int:
        return date_or_ts
    return int(date_or_ts.timestamp() * 1000)
