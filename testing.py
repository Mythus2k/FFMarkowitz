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

def build_frontier(tick):
    ret = rf + tick['beta']*(mr-rf)
        
    pw = []
    tw = []
    er = []
    std = []

    for weight in range(0,100,1):
        pw.append(weight/100)
        tw.append(1-pw[-1])

        er.append((pw[-1]*ptf['ret'])+(tw[-1]*ret))
        std.append(sqrt((pw[-1]**2*ptf['std']**2)+(tw[-1]**2*tick['std']**2)+(ptf['beta']*tick['beta']*mstd**2)))
        
    perform = DataFrame({'pw':pw,'tw':tw,'er':er,'std':std})

    return perform

if __name__ == '__main__':
    td = Ticker_Deamon()
    td.add_tick('bac')
    td.add_tick('tsla')
    td.add_tick('v')
    td.add_tick('xom')
    td.add_tick('COO')
    td.add_tick('ilmn')
    td.add_tick('algn')
    td.add_tick('hrl')
    td.add_tick('cost')
    td.add_tick('lumn')
    td.add_tick('nvda')
    td.add_tick('ai')
    td.add_tick('bkng')
    td.add_tick('gww')
    td.add_tick('fslr')
    td.add_tick('lin')
    td.add_tick('uri')
    td.add_tick('f')
    td.add_tick('glpg')

    mr = .08
    rf = .04
    mstd = td.index['std']

    ptf = {}

    df = td.tickers.T
    tick = df.pop(0)

    ptf['ret'] = rf + tick['beta']*(mr-rf)
    ptf['beta'] = tick['beta']
    ptf['std'] = tick['std']
    ptf['ticks'] = {tick['ticker']:1}

    for col in df.columns:
        # print(df.T)
        # print('current ptf: ',ptf)
        tick = df.pop(col)

        perform = build_frontier(tick)

        perform['slope'] = (rf-perform['er'])/(-perform['std'])
        efficient = perform.loc[perform['slope'] == perform['slope'].max()]
        efficient.reset_index(inplace=True)

        
        # pyplot.plot(perform['std'],perform['er'])
        # pyplot.scatter(efficient['std'],efficient['er'])
        # pyplot.show()

        ptf['ret'] = efficient['er'][0]
        ptf['std'] = efficient['std'][0]
        ptf['beta'] = (ptf['ret']-rf)/(mr-rf)

        for ticks in ptf['ticks']:
            ptf['ticks'][ticks] = ptf['ticks'][ticks] * efficient['pw'][0]
        
        ptf['ticks'][tick['ticker']] = efficient['tw'][0]

        print('ptf ret: ',ptf['ret'],'   ptf std:',ptf['std'])
    print(ptf['ticks'])


