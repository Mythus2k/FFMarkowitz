import yfinance as yf
from pandas import Timestamp, DataFrame, concat
from sklearn.linear_model import LinearRegression
from numpy import array
from pickle import load, dump

def now():
    "Returns pandas.Timestamp.now('US/Eastern')"
    return Timestamp.now('US/Eastern')

class TickerDaemon:
    # init
    def __init__(self, period = '10y', interval = '1mo', ohlc = 'Adj Close') -> None:
        # download params
        self.period = period
        self.interval = interval
        self.ohlc = ohlc
        # index params
        self.index = 'vti'
        self.index_data = DataFrame()
        self.index_return = DataFrame()
        self.index_variance = DataFrame()
        # ticker params
        self.tickers = set() 
        self.ticker_data = DataFrame()
        self.ticker_return = DataFrame()
        self.ticker_variance = DataFrame()
        self.ticker_beta = DataFrame()

        print(f'TickerDaemon ready')

    def __str__(self):
        return f"""================= Ticker Daemon info =================
period: {self.period}
interval: {self.interval}
OHLC: {self.ohlc}
index: {self.index}
tickers: {self.tickers}
ticker data (decimal): \n{concat([self.ticker_beta,self.ticker_return,self.ticker_variance])}
====================== End Info ======================"""

    def add_ticker(self, ticker):
        self.tickers.add(ticker.upper())
        print(f'added {ticker.upper()}')

    def delete_ticker(self, ticker):
        self.tickers.remove(ticker.upper())
        print(f'removed {ticker.upper()}')

    def clear_tickers(self):
        self.tickers.clear()
        print(f'cleared all tickers')

    def download_data(self):
        data = yf.download(list(self.tickers)+[self.index],period=self.period,interval=self.interval)[self.ohlc].pct_change().dropna()
        
        if data.empty:
            print(f'Failed download. See above for error info')
            if input('Download individually? (Y/N):  ').upper() == 'Y':
                data = DataFrame()
                temp = DataFrame()
                for _ in list(self.tickers)+[self.index]:
                    temp = yf.download(_,period=self.period,interval=self.interval)[self.ohlc].pct_change().dropna()
                    data[_.upper()] = temp
            else:
                return
        
        self.index_data = data.pop(self.index.upper())
        self.ticker_data = data
        print(f'all data downloaded')

    def download_timeframe_data(self, start, end):
        """
        for testing - not for gui
        
        start: str
         Download start date string (YYYY-MM-DD) or _datetime. Default is 1900-01-01
        end: str
         Download end date string (YYYY-MM-DD) or _datetime. Default is now
        """
        data = yf.download(list(self.tickers)+[self.index],start=start,end=end)[self.ohlc].pct_change().dropna()
        
        if data.empty:
            print(f'Failed download. See above for error info')
            if input('Download individually? (Y/N):  ').upper() == 'Y':
                data = DataFrame()
                temp = DataFrame()
                for _ in list(self.tickers)+[self.index]:
                    temp = yf.download(_,start,end)[self.ohlc].pct_change().dropna()
                    data[_.upper()] = temp
            else:
                return
        
        self.index_data = data.pop(self.index.upper())
        self.ticker_data = data
        print(f'data download complete')

    def calc_returns(self):
        out = DataFrame()

        df = self.ticker_data
        df[self.index.upper()] = self.index_data
    
        years = (df.iloc[-1].name - df.iloc[0].name).days/365
        
        for tick in df.columns:
            out[tick] = [df[tick].sum()/years]

        out.index = ['Return']
        self.index_return = out.pop(self.index.upper())
        self.ticker_return = out

        print('Expected returns solved')

    def calc_variance(self):
        out = DataFrame()

        df = self.ticker_data
        df[self.index.upper()] = self.index_data

        out = DataFrame(df.var()).T

        out.index = ['Variance']
        self.index_variance = out.pop(self.index.upper())
        self.ticker_variance = out

        print('Variances solved')

    def calc_beta(self):
        # beta = LinearRegression().fit(bdata[['x']],bdata[['y']]).coef_[0][0]
        out = DataFrame()
        y = array(self.index_data.to_list()).reshape([-1,1])

        for ticker in self.tickers:
            x = array(self.ticker_data[ticker].to_list()).reshape([-1,1])
            out[ticker] = [LinearRegression().fit(x,y).coef_[0][0]]

        out.index = ['Beta']
        self.ticker_beta = out

        print('betas solved')

    def save(self):
        dump(self,open('./Conf/TickerDaemon.conf','wb'))

if __name__ == '__main__':
    td = TickerDaemon()
    
    td.period = '10y'
    td.interval = '3mo'
    td.index = 'vti'

    print(td)

    td.add_ticker('bac')
    td.add_ticker('xom')
    td.add_ticker('tsla')
    td.add_ticker('meta')

    td.download_data()

    td.calc_returns()
    
    td.calc_variance()

    td.calc_beta()
    
    print(td)
    td.save()