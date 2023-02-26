from yfinance import download as yfdown
from pandas import read_csv, DataFrame, Timestamp
from pickle import load, dump
from sklearn.linear_model import LinearRegression

def now():
    "Returns pandas.Timestamp.now('US/Eastern')"
    return Timestamp.now('US/Eastern')

class Ticker_Deamon:
    # initalize
    def __init__(self):
        # create tickers list
        self.tickers = DataFrame({
            'ticker': list(),
            'std': list(),
            'beta': list(),
            'last_update': list()
        })       
        self.dump_tickers()

        # Parameters
        self.period = '10y'
        self.interval = '1mo'
        self.ohcl = 'Close'
        
        # create index
        self.index = dict()
        self.set_index('vti')
        
    def reload_ticks(self):
        self.tickers = read_csv('./tickers.csv')
        return

    def recalc_ticks(self):
        ticks = self.tickers['ticker'].to_list()
        for tick in ticks:
            self.del_tick(tick)
            self.add_tick(tick)
        
        return

    def dump_tickers(self):
        self.tickers.to_csv('./tickers.csv',index=False)
        return

    def add_tick(self, tick):
        calc = self.calc(tick)

        self.tickers.loc[-1] = {'ticker':tick,'std':calc[0],'beta':calc[1],'last_update':now()}
        self.tickers.index = self.tickers.index + 1
        self.tickers.reset_index(inplace=True, drop = True)
        self.dump_tickers()
        
        return 

    def del_tick(self, tick):
        self.tickers = self.tickers.drop(self.tickers.loc[self.tickers['ticker'] == tick].index[0])
        self.dump_tickers()

        return

    def update_tick(self, tick):
        pass

    def truncate_data(self, tick, length):
        pass

    def calc(self, tick):
        bdata = DataFrame()
        data = yfdown(tick, period=self.period, interval=self.interval)[[self.ohcl]].dropna()

        bdata['y'] = data.pct_change().dropna()
        bdata['x'] = self.index['data'].pct_change().dropna()

        bdata = bdata.dropna()

        std = bdata['y'].std()
        beta = LinearRegression().fit(bdata[['x']],bdata[['y']]).coef_[0][0]

        return (std, beta)

    def set_index(self, tick):
        self.index['ticker'] = tick
        self.index['data'] = yfdown(tick,period=self.period,interval=self.interval)[[self.ohcl]].dropna()
        self.index['std'] = self.index['data'].pct_change().dropna()[self.ohcl].std()
        self.index['date'] = now()

        self.recalc_ticks()

        return 

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

    def set_ohcl(self, ohcl):
        '''
        Must be:
            Open, High, Low, Close, Adj Close
        '''
        self.ohcl = ohcl

    def dump_tickDeamon(self):
        dump(self,open('./Conf/TickerDeamon.conf','wb'))


class Markowitz_Deamon:
    def __init__(self) -> None:
        self.td = Ticker_Deamon()
        self.rf = float()
        self.mr = float()
        self.set_riskFree(.04) # need to remove from .04 to
        self.set_marketReturn(.08)

        self.mMatrix = DataFrame()
    
    # Needs work inside
    def set_riskFree(self,rate=None):
        if rate == None:
            # Devolpe call from treasury website to pull relevant RF ratge
            print('go out and find riskfree from treasury site')
            # rate = n_rate
        self.rf = rate

    # Needs work inside
    def set_marketReturn(self, marketReturn = None):
        if marketReturn == None:
            # need to add code to create a PY // avg market return
            print('Go out and find market return')
        self.mr = marketReturn
    
    # def 

    # return covariance
    
    # risk aversion

    # shorting?

    # any additional limits!

if __name__ == '__main__':
    md = Markowitz_Deamon()
    md.td.add_tick('bac')
    md.td.add_tick('tsla')
    md.td.add_tick('v')
    md.td.add_tick('xom')

    print(md.td.tickers)
    
    mvar = md.td.index['std']**2
    print(mvar)
    svar = md.td.tickers.iloc[0]['std']**2
    print(svar)

    exp_ret = []
    weight = []

    start_weights = 1/len(md.td.tickers)
    print(start_weights)

    
    
    

