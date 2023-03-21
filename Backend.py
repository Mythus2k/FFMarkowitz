import yfinance as yf
from pandas import Timestamp, DataFrame

def now():
    "Returns pandas.Timestamp.now('US/Eastern')"
    return Timestamp.now('US/Eastern')

class TickerDaemon:
    # init
    def __init__(self, period = '10y', interval = '1mo', ohcl = 'Adj Close') -> None:
        # parameters for data
        self.period = period
        self.interval = interval
        self.ohcl = ohcl
        self.index = str()
        self.tickers = set() 

    def add_ticker(self, ticker):
        self.tickers.add(ticker)

    def delete_ticker(self, ticker):
        self.tickers.remove(ticker)

    def clear_tickers(self):
        self.tickers.clear()

    