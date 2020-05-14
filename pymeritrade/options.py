import pandas as pd

from pymeritrade.errors import TDAAPIError
from pymeritrade.utils import parse_date_cols


JSON_KEY_MAP = {
    'symbol': 'option_symbol',
    'putCall': 'contract',
    'highPrice': 'high',
    'lowPrice': 'low',
    'openPrice': 'open',
    'closePrice': 'close',
    'strikePrice': 'strike',
    'totalVolume': 'volume',
    'inTheMoney': 'itm',
    'bidSize': 'bid_size',
    'askSize': 'ask_size',
    'timeValue': 'time_value',
    'daysToExpiration': 'days_to_exp',
    'nonStandard': 'nonstandard',
    'bidAskSize': 'bid_ask_size',
    'openInterest': 'open_interest',
    'tradeTimeInLong': 'trade_time',
    'quoteTimeInLong': 'quote_time',
    'lastTradingDay': 'last_trade_date',
    'expirationDate': 'exp_date',
    'tradeDate': 'trade_date',
    'theoreticalOptionValue': 'theoretical_value',
    'theoreticalVolatility': 'theoretical_volatility',
    'expirationType': 'exp_type',
    'exchangeName': 'exchange'
}


class TDAOptions:

    def __init__(self, client, **kwargs):
        self.client = client
        self.parse_dates = kwargs.get('parse_dates', True)
        self.range = kwargs.get('range')
        self.contracts = kwargs.get('contracts', 'all')
        self.quotes = kwargs.get('quotes', True)
        self.strategy = kwargs.get('strategy', 'single')
        self.strike = kwargs.get('strike')
        self.exp_month = kwargs.get('exp_month', 'all')

    def _call_api(self, symbol):
        params = dict(
            symbol=symbol,
            contractType=self.contracts.upper(),
            includeQuotes=str(self.quotes).upper(),
            strategy=self.strategy.upper(),
            expMonth=self.exp_month.upper()
        )
        if self.strike is not None:
            params['strike'] = self.strike
        if self.range is not None:
            params['strikeCount'] = self.range
        resp = self.client._call_api('marketdata/chains'.format(symbol), params=params)
        options_all = []
        for key in ['callExpDateMap', 'putExpDateMap']:
            for exp, strikes in resp.get(key, {}).items():
                for strike, options in strikes.items():
                    options_all.extend(options)
        df = pd.DataFrame(options_all)
        df = df.rename(columns=JSON_KEY_MAP)
        df['symbol'] = symbol
        df['interest_rate'] = resp['interestRate']
        if self.parse_dates:
            df = parse_date_cols(df, ['exp_date', 'trade_time', 'quote_time', 'last_trade_date'])
        df['overall_volatility'] = resp['volatility']
        df['overall_strategy'] = resp['strategy']
        df['vol_by_oi'] = df['volume'] / df['open_interest']
        df = df.set_index('option_symbol')
        return df

    def __getitem__(self, key):
        return self._call_api(key)