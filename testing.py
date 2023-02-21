from yfinance import download as yfdown
from pandas import read_csv, DataFrame, Timestamp
from pickle import load, dump

def now():
    "Returns pandas.Timestamp.now('US/Eastern')"
    return Timestamp.now('US/Eastern')

class Ticker_Deamon:
    # initalize
    def __init__(self):
        # create DataFrame
        self.tickers = DataFrame({
            'ticker': list(), 
            'beta': list(), 
            'std': list(), 
            'last_update': list(),
            'period': list(),
            'interval': list()})            
        self.tickers.to_csv('tickers.csv',index=False)

        # create index
        self.period = '10y'
        self.interval = '1mo'
        
        self.index = {
            'ticker' : 'vti', 
            'data' : yfdown('vti',period=self.period,interval=self.interval),
            'date' : now()}
        

    # Add tickers
    def add_tick(self, tick):
        new_tick = {
            'ticker': tick,
            'beta': None,
            'std': None,
            'last_update': now(),
            'period': None,
            'interval': None}
        
        data = yfdown(tick,period=self.period,interval=self.interval)


        self.tickers += new_tick
        
        return tick

    # remove tickers
    def del_tick(self, tick):
        pass

    # update data
    def update_tick(self, tick):
        pass

    # truncate data
    def truncate_data(self, tick, length):
        pass

    # set data history
    def set_dataLen(self, tick, length):
        pass

    # calculate points
    def calc(self, tick):
        beta = float()
        std = float()
        date = str()
        pick = None

        return beta, std, date, pick

    def set_index(self, tick):
        self.index['ticker'] = tick
        self.index['data'] = yfdown(tick,period=self.period,interval=self.interval)
        self.index['date'] = now()

    def set_period(self, period):
        """
        period must be: 
            1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        """
        self.period = period

    def set_interval(self, interval):
        """
        interval must be:
            1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo

        Intraday data cannot extend last 60 days.
        """
        self.interval = interval


class Markowitz_Deamon:
    pass
    # read ticker data

    # set index

    # set risk free

    # call risk free

    # set market return

    # return covariance

    # risk aversion

    # any additional limits!

if __name__ == '__main__':
    print(now())