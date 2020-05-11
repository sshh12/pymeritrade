# pymeritrade

> A python interface for using the TD Ameritrade API.

```shell
$ pip install git+https://github.com/sshh12/pymeritrade
```

## Usage

```python
from pymeritrade import TDAClient

api_key = 'FANISDI42KS53AD...'

tda = TDAClient(api_key)
# first time login
tda.login()
tda.save_login()
# normal login
tda.load_login()

print(tda.account)
print(tda.day_trades)
print(tda.liquidation_value)
print(tda.options(quotes=True)['AAPL'])
```

```python
stream = tda.create_stream(debug=True)
stream.start()

stream.subscribe('news', symbols=['AAPL', 'AMZN'])
stream.subscribe('quote', symbols=['AMZN'])
stream.subscribe('forex', symbols=['EUR/USD'])
stream.subscribe('chart', type='equity', symbols=['AMZN'])
stream.subscribe('actives', exchange='NASDAQ', symbols=['NASDAQ-60'])
for item in stream.live_data():
    print(item)
```

```python
# Create a history factory (symbol(s) -> Pandas DataFrame)
# spans {day, month, year, ytd}
# freqs {minute, daily, weekly, monthly}
daily_history       = tda.history(span='year', freq='daily')
daily_history_no_ah = tda.history(span='year', freq='daily', extended=False)
old_history         = tda.history(span='year', freq='daily', start=datetime(2000, 1, 1))
high_res_history    = tda.history(span='day', freq='minute')

# Get single symbol history
daily_history['AAPL']

# Get multi symbol history
daily_history[['AAPL', 'INTC']]
#                      AAPL_open  AAPL_high  AAPL_low  AAPL_close  ...  INTC_high  INTC_low  INTC_close  INTC_volume
# datetime                                                         ...
# 2019-05-08 05:00:00    201.900     205.34  201.7500      202.90  ...    50.7900     49.07       49.24     36812429
# 2019-05-09 05:00:00    200.400     201.68  196.6600      200.72  ...    48.2900     46.05       46.62     59642160
# 2019-05-10 05:00:00    197.419     198.85  192.7700      197.18  ...    46.8000     45.10       46.20     42522778
# 2019-05-13 05:00:00    187.710     189.48  182.8500      185.72  ...    45.6400     44.70       44.76     39091928
# 2019-05-14 05:00:00    186.410     189.70  185.4100      188.66  ...    45.4850     44.87       45.17     24706458
# ...                        ...        ...       ...         ...  ...        ...       ...         ...          ...
# 2020-05-04 05:00:00    289.170     293.69  286.3172      293.16  ...    58.0700     56.31       57.99     18957227
# 2020-05-05 05:00:00    295.060     301.00  294.4600      297.56  ...    59.3000     58.35       58.75     17252063
# 2020-05-06 05:00:00    300.460     303.24  298.8700      300.63  ...    59.9500     58.94       59.18     17848655
# 2020-05-07 05:00:00    303.220     305.17  301.9700      303.74  ...    60.0969     58.92       59.17     14733519
# 2020-05-08 05:00:00    305.640     310.35  304.2900      310.13  ...    59.7800     59.05       59.67     20391091
```

## Alternative Python Libs

[@areed1192/td-ameritrade-python-api](https://github.com/areed1192/td-ameritrade-python-api)
[@timkpaine/tdameritrade](https://github.com/timkpaine/tdameritrade)