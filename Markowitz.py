from yfinance import download as yfdown
from pandas import read_csv, DataFrame, Timestamp
from pickle import load, dump
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot
from math import sqrt

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
        # self.dump_tickers()

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
        # self.dump_tickers()
        
        return 

    def del_tick(self, tick):
        self.tickers = self.tickers.drop(self.tickers.loc[self.tickers['ticker'] == tick].index[0]).reset_index(drop=True)
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

    def annualize_return(self, data):
        new = data.iloc[-1]
        old = data.iloc[0]
        
        ret = (new[self.ohcl]-old[self.ohcl])/old[self.ohcl]
        years = (new.name - old.name).days/365
        annualized = ret/years

        return annualized

    def set_index(self, tick):
        self.index['ticker'] = tick
        self.index['data'] = yfdown(tick,period=self.period,interval=self.interval)[[self.ohcl]].dropna()
        self.index['std'] = self.index['data'].pct_change().dropna()[self.ohcl].std()
        self.index['return'] = self.annualize_return(self.index['data'])
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


class Markowitz_Deamon():
    def __init__(self) -> None:
        self.td = Ticker_Deamon()
        self.rfd = {}
        self.rf = float()
        self.mstd = self.td.index['std']
        self.mr = self.td.index['return']
        self.ptf = {}
        self.perform = None
        self.efficient = None
        self.ptf_x = 0
        self.ptf_y = .04
        self.investing = 1000

    def set_index(self, tick):
        self.td.set_index(tick)
        self.mstd = self.td.index['std']
        self.mr = self.td.index['return']

    def set_riskfree(self, tick):
        """
        ticks must be:
            "^IRX" - 13 weeks
            "^FVX" -  5 year
            "^TNX" - 10 year
            "^TYX" - 30 year
        """
        self.rfd['ticker'] = tick
        self.rfd['data'] = yfdown(tick,period=self.td.period,interval=self.td.interval)[[self.td.ohcl]].dropna()/100
        self.rfd['rate'] = self.rfd['data'].iloc[-1]['Close']
        self.rfd['date'] = now()

        self.rf = self.rfd['rate']

    def add_tick(self, tick):
        self.td.add_tick(tick)
    
    def del_tick(self, tick):
        self.td.del_tick(tick)

    def build_frontier(self, tick):
        ret = self.rf + tick['beta']*(self.mr-self.rf)
            
        pw = []
        tw = []
        er = []
        std = []

        for weight in range(0,100,1):
            pw.append(weight/100)
            tw.append(1-pw[-1])

            er.append((pw[-1]*self.ptf['ret'])+(tw[-1]*ret))
            std.append(sqrt((pw[-1]**2*self.ptf['std']**2)+(tw[-1]**2*tick['std']**2)+(self.ptf['beta']*tick['beta']*self.mstd**2)))
            
        perform = DataFrame({'pw':pw,'tw':tw,'er':er,'std':std})

        return perform

    def build_ptf(self):
        self.ptf = {}

        df = self.td.tickers.T
        tick = df.pop(0)

        self.ptf['ret'] = self.rf + tick['beta']*(self.mr-self.rf)
        self.ptf['beta'] = tick['beta']
        self.ptf['std'] = tick['std']
        self.ptf['ticks'] = {tick['ticker']:1}

        for col in df.columns:
            tick = df.pop(col)

            perform = self.build_frontier(tick)

            perform['slope'] = (self.rf-perform['er'])/(-perform['std'])
            efficient = perform.loc[perform['slope'] == perform['slope'].max()]
            efficient.reset_index(inplace=True)

            # print(perform['slope'])
            # print(efficient)
            # pyplot.plot(perform['std'],perform['er'])
            # pyplot.scatter(efficient['std'],efficient['er'])
            # pyplot.show()

            self.ptf['ret'] = efficient['er'][0]
            self.ptf['std'] = efficient['std'][0]
            self.ptf['beta'] = (self.ptf['ret']-self.rf)/(self.mr-self.rf)

            for ticks in self.ptf['ticks']:
                self.ptf['ticks'][ticks] = self.ptf['ticks'][ticks] * efficient['pw'][0]
            
            self.ptf['ticks'][tick['ticker']] = efficient['tw'][0]
            
            self.perform = perform
            self.efficient = efficient

    def save(self):
        dump(self,open('./Conf/markowitz.conf','wb'))

if __name__ == '__main__':
    m = Markowitz_Deamon()

    m.set_index('vti')
    m.set_riskfree('^IRX')
    m.add_tick('tsla')
    m.add_tick('v')
    m.add_tick('xom')

    m.build_ptf()
    print(m.ptf)
    m.save()