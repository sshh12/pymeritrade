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

## Alternative Python Libs

[@areed1192/td-ameritrade-python-api](https://github.com/areed1192/td-ameritrade-python-api)
[@timkpaine/tdameritrade](https://github.com/timkpaine/tdameritrade)