from yfinance import download as yfdown
from pandas import read_csv, DataFrame, Timestamp, concat
from pickle import load, dump
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot
from math import sqrt
import cvxpy as cp
import numpy as np

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

    def build_ptf_deprecated(self):
        self.ptf = {}

        # Sort dataframe of tickers by alternating betas
        df = self.td.tickers.sort_values('beta').reset_index(drop=True)
        # even len
        if len(df) % 2 == 0:
            l = len(df)
            temp = DataFrame()
            for o in range(int(l/2)):
                temp = concat([temp, df[df.index == o]])
                temp = concat([temp, df[df.index == (l-o-1)]])
        # uneven len
        else:
            l = len(df)
            temp = DataFrame()
            for o in range(int(l/2)):
                temp = concat([temp, df[df.index == o]])
                temp = concat([temp, df[df.index == (l-o-1)]])
            temp = concat([temp, df[df.index == int(l/2)]])
    
        # Calculate curves and stuff
        df = temp.iloc[::-1].T
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

            # pyplot commented out - not in venv
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

    def step_calc(self, data, step):
        l = len(data.index)
        neg = list()
        pos = list()
        out = list()

        for _ in range(1,1+int(l/2)):
            neg.append(-step/_)
            pos.append(step/_)

        if l % 2 == 0:
            for _ in neg:
                out.append(_)
            for _ in pos:
                out.append(_)
        
        else:
            for _ in neg:
                out.append(_)
            out.append(0)
            for _ in pos:
                out.append(_)

        return out

    def build_ptf(self,runs=2000,step=.003):
        data = self.td.tickers.set_index('ticker',drop=True).drop('last_update',axis=1)

        mult = dict()
        for tick in data.index:
            mult[tick] = 1

        step = self.step_calc(data, step)
        finished = False
        check_var = list()
        check_ret = list()

        for _ in range(runs):
            # weights
            niave = dict()
            for tick in data.index:
                niave[tick] = (1/len(data.index))

            w_ = DataFrame({'niave':niave, 'mult':mult}).set_index(data.index)

            w_['weight'] = w_['niave']* w_['mult']
            
            # leveraging check
            if w_['weight'].min() < 0:
                # print('weight going into leverage')
                # print(f"run {_}/{runs}")
                # print(weight)
                # print(f"ptf var: {ptf_var:.2%}")
                # print(f"ptf ret: {ptf_ret:.2%}")
                # print('weights solved')
                break

            # returns
            r_ = list()
            for tick in data.index:
                r_.append(self.rf + data['beta'][tick]*(self.mr-self.rf))

            r_ = DataFrame({'return':r_}).set_index(data.index)

            # solve covariance matrix
            cvar = dict()
            for tick in data.index:
                hvar = list()
                for tick_ in data.index:
                    covar = (data['beta'][tick] * data['beta'][tick_] * (self.mstd**2))
                    hvar.append(w_['weight'][tick] * w_['weight'][tick_] * covar)
                
                cvar[tick] = hvar

            v_ = DataFrame(cvar).set_index(data.index)

            # update weight multiplier
            update_mults = v_.sum().sort_values().reset_index(name='std').drop('std',axis=1)
            for i in update_mults.index:
                mult[update_mults['index'][i]] += step[i]
            
            # outputs
            ptf_ret = (r_['return'] * w_['weight']).sum()
            ptf_std = sqrt(v_.sum().sum())

            weight = w_

            # updates for cmd
            # if _ % 200 == 0:
            #     print(f"run {_}/{runs}")
            #     print(weight)
            #     print(f"ptf std: {ptf_std:.2%}")
            #     print(f"ptf ret: {ptf_ret:.2%}")

        # graphing
        y_ = r_
        x_ = data['std'].to_list()

        # pyplot.scatter(x_,y_)
        # pyplot.scatter(ptf_std,ptf_ret)
        # pyplot.show()

        self.ptf = {'ret':ptf_ret,'std':ptf_std,'ticks':weight['weight'].to_dict()}

    def save(self):
        dump(self,open('./Conf/markowitz.conf','wb'))


def reset_gui():
    m = Markowitz_Deamon()

    m.set_index('vti')
    m.set_riskfree('^IRX')
    m.add_tick('tsla')
    m.add_tick('v')
    m.add_tick('xom')
    m.add_tick('meta')
    m.add_tick('bac')

    m.build_ptf()
    print(m.ptf)
    m.save()


if __name__ == '__main__':
    # m = load(open('./Conf/Markowitz.conf','rb'))

    # m.build_ptf()
     
    reset_gui()