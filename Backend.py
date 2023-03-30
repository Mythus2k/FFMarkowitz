import random
from math import sqrt
from pickle import dump, load

import yfinance as yf
from matplotlib import pyplot
from numpy import array
from pandas import DataFrame, Timestamp, concat, read_csv
from sklearn.linear_model import LinearRegression


def now():
    "Returns pandas.Timestamp.now('US/Eastern')"
    return Timestamp.now('US/Eastern')

class PtfDaemon:
    # init
    def __init__(self, period = '10y', interval = '1mo', risk_free = '^TNX', ohlc = 'Adj Close') -> None:
        # download params
        self.period = period
        self.interval = interval
        self.ohlc = ohlc
        # risk free params
        self.risk_free = str()
        self.risk_free_rate = float()
        self.set_risk_free_rate(risk_free)
        self.risk_adjuster = 1
        # index params
        self.index = 'VTI'
        self.index_data = DataFrame()
        self.index_return = DataFrame()
        self.index_variance = DataFrame()
        # ticker params
        self.tickers = set() 
        self.ticker_data = DataFrame()
        self.ticker_return = DataFrame()
        self.ticker_variance = DataFrame()
        self.ticker_beta = DataFrame()
        # solver params
        self.weights = DataFrame()
        self.ptf_return = float()
        self.ptf_variance = float()
        self.ptf_rf_slope = -999
        self.covariance_matrix = DataFrame()

        print(f'TickerDaemon ready')

    def __str__(self):
        string =  f"\n================= Ticker Daemon info =================\n"
        string += f"period: {self.period}\n"
        string += f"interval: {self.interval}\n"
        string += f"OHLC: {self.ohlc}\n"
        string += f"index: {self.index}\n"
        string += f"risk free: {self.risk_free}\n"
        string += f"risk free rate: {self.risk_free_rate:.2%}\n"
        string += f"Desired return adjuster: {self.risk_adjuster/100:.2%}\n"
        string += f"ptf return: {self.ptf_return:.2%}\n"
        string += f"ptf std: {sqrt(self.ptf_variance):.2%}\n"
        string += f"ptf weights (as decimal): \n{self.weights.T}\n"
        string += f"tickers (as decimal): \n{concat([self.ticker_beta,self.ticker_return,self.ticker_variance])}\n"
        string += f"====================== End Info ======================\n"
        return string

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
        data = yf.download(list(self.tickers)+[self.index],period=self.period,interval=self.interval)[self.ohlc].dropna().pct_change().dropna()[:-1]
        # print(data.describe())
        # print(data.cov())
        # exit()
        
        if data.empty:
            print(f'Failed download. See above for error info')
            if input('Download individually? (Y/N):  ').upper() == 'Y':
                data = DataFrame()
                temp = DataFrame()
                for _ in list(self.tickers)+[self.index]:
                    temp = yf.download(_,period=self.period,interval=self.interval)[self.ohlc].dropna().pct_change().dropna()[:-1]
                    if not temp.empty:
                        data[_.upper()] = temp
                    else:
                        self.delete_ticker(_.upper())
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
        data = yf.download(list(self.tickers)+[self.index],start=start,end=end)[self.ohlc].dropna().pct_change().dropna()[:-1]
        
        if data.empty:
            print(f'Failed download. See above for error info')
            if input('Download individually? (Y/N):  ').upper() == 'Y':
                data = DataFrame()
                temp = DataFrame()
                for _ in list(self.tickers)+[self.index]:
                    temp = yf.download(_,start,end)[self.ohlc].dropna().pct_change().dropna()[:-1]
                    if not temp.empty:
                        data[_.upper()] = temp
                    else:
                        self.delete_ticker(_.upper())
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

        print('Expected returns solved: ')
        print(self.ticker_return)

    def calc_variance(self):
        out = DataFrame()

        df = self.ticker_data
        df[self.index.upper()] = self.index_data

        out = DataFrame(df.var()).T

        out.index = ['Variance']
        self.index_variance = out.pop(self.index.upper())
        self.ticker_variance = out

        print('Variances solved: ')
        print(self.ticker_variance)

    def calc_beta(self):
        # beta = LinearRegression().fit(bdata[['x']],bdata[['y']]).coef_[0][0]
        out = DataFrame()
        x = array(self.index_data.to_list()).reshape([-1,1])

        for ticker in self.tickers:
            y = array(self.ticker_data[ticker].to_list()).reshape([-1,1])
            out[ticker] = [LinearRegression().fit(x,y).coef_[0][0]]

        out.index = ['Beta']
        self.ticker_beta = out

        print('betas solved: ')
        print(self.ticker_beta)

    def set_risk_free_rate(self,ticker,date=-1):
        """
        ticks must be:
            "^IRX" - 13 weeks
            "^FVX" -  5 year
            "^TNX" - 10 year
            "^TYX" - 30 year
        date : any
            date formate (YYYY-MM-DD)
        """
        self.risk_free = ticker
        self.risk_free_rate = yf.download(ticker,period=self.period,interval=self.interval)['Adj Close'][date]/100
        print(f"Risk free set to {self.risk_free} with a rate of {self.risk_free_rate:.2%}")

    def solve_cov_matrix(self, weights_frame):
        covariance_matrix = self.ticker_data.drop(self.index.upper(),axis='columns').cov()
        for tick in covariance_matrix.index:
            col = list()
            for tick_ in covariance_matrix.index:
                col.append(weights_frame[tick] * weights_frame[tick_] * covariance_matrix[tick][tick_])
            covariance_matrix[tick] = col

        return covariance_matrix

    def weights_updater(self, covariance_matrix,update_range=5):
        # set up data
        weight_update = self.weights['Weights']
        covariance_matrix = covariance_matrix.sum().sort_values()
        
        # randomize the matrix
        covariance_matrix = covariance_matrix.sample(len(covariance_matrix))
        
        # Create a dataframe to to use to make updating decisions
        df = concat((covariance_matrix,weight_update),axis=1)
        df.columns = ['Covar','Weights']
        df['Index'] = [_ for _ in range(len(df))]

        # randomly decrease bottom half, randomly increase top half
        weights = df['Weights'].to_dict()
        for tick in weights.keys():
            if df['Index'][tick] < len(df)/2:
                weights[tick] = weights[tick] * (random.randrange(100-update_range,100)/100)
            else:
                weights[tick] = weights[tick] * (random.randrange(100,100+update_range)/100)
        
        df['Weights'] = weights.values()

        # Normalize weights to sum to 100
        df['Weights'] = [w / df['Weights'].sum() for w in df['Weights']]
        
        # return only the weights as a DataFrame
        return df['Weights']

    def solve(self,runs=200,weight_adjust=99):
        # checks tracker
        tracker_all = {'ret':list(),'var':list()}
        tracker_used = {'ret':list(),'var':list()}

        # set up weights
        # weights = [round(random.random(),4) for _ in range(len(self.tickers))]  # Random weights
        # self.weights['Weights'] = [w / sum(weights) for w in weights]           # Random weights
        self.weights['Weights'] = [1/len(self.tickers) for _ in self.tickers]     # Niave weights 
        self.weights.index = self.tickers

        # assign high value for variance comparision initalization
        self.ptf_variance = 999

        for _ in range(runs):
            # solve covariance matrix
            covariance_matrix = self.solve_cov_matrix(self.weights['Weights'])

            # update weights
            weight_update = self.weights_updater(covariance_matrix,weight_adjust)
            
            # Get new values
            new_ret = (self.ticker_return.T['Return'] * weight_update).sum()
            new_var = self.solve_cov_matrix(weight_update).sum().sum()

            # rf_slope_check
            slope = ((self.risk_free_rate - new_ret)/(0 - sqrt(new_var))) - self.risk_free_rate
            slope_check = slope > self.ptf_rf_slope            

            # update outputs if improvement over previous position
            # if ret_check or var_check:
            if slope_check:
                self.weights['Weights'] = weight_update
                self.ptf_return = (self.ticker_return.T['Return'] * self.weights['Weights']).sum()
                self.ptf_variance = covariance_matrix.sum().sum()
                self.ptf_rf_slope = (self.risk_free_rate - self.ptf_return) / (0 - sqrt(self.ptf_variance))
                
                # update the used list for plotting
                tracker_used['ret'].append(self.ptf_return)
                tracker_used['var'].append(self.ptf_variance)

            # track all tested
            tracker_all['ret'].append((self.ticker_return.T['Return'] * self.weights['Weights']).sum())
            tracker_all['var'].append(covariance_matrix.sum().sum())

            # intermitten checking
            if _ % int(runs/10)-1 == 0:
                print(f"run {_}/{runs}")
                print(f"old slope: {self.ptf_rf_slope:.5}")
                print(f"new slope: {slope:.5}")
                print(f"slope_check result: {slope_check}")
                print(f"ptf return: {self.ptf_return:.2%}")
                print(f"ptf std: {sqrt(self.ptf_variance):.2%}")
                print(f"ptf weights (top 10):")
                print((td.weights['Weights']*100).sort_values(ascending=False).head(10))
                print(f"===== End Check =====\n")

        return tracker_all, tracker_used

    def save(self):
        dump(self,open('./Conf/ptf_Daemon.conf','wb'))

if __name__ == '__main__':
    td = PtfDaemon(risk_free='^IRX')
    
    td.period = '10y'
    td.interval = '1mo'
    td.index = 'spy'

    # standard set
    # td.add_ticker('bac')
    # td.add_ticker('xom')
    # td.add_ticker('tsla')
    # td.add_ticker('meta')
    # td.add_ticker('msft')
    # td.add_ticker('v')

    # my ptf test
    td.add_ticker('vti')
    td.add_ticker('vxus')
    td.add_ticker('ffrhx')
    td.add_ticker('xle')
    td.add_ticker('inda')
    td.add_ticker('farmx')
    td.add_ticker('fsdpx')
    td.add_ticker('intc')
    td.add_ticker('pick')
    td.add_ticker('aapl')
    td.add_ticker('meta')
    td.add_ticker('umc')
    td.add_ticker('wu')
    
    # spy test - working - some assets give really weird results, might not have full history
    # spy = read_csv('spy.csv')
    # for tick in spy['Symbol'].sample(300):
    #     td.add_ticker(tick)    

    td.download_data()

    td.calc_returns()
    
    td.calc_variance()

    td.calc_beta()

    tracker_all, tracker_used = td.solve(runs=200,weight_adjust=99)

    # data outputs
    print('========================  Output  ==========================')
    print(f"ptf return: {td.ptf_return:.2%}")
    print(f"ptf std: {sqrt(td.ptf_variance):.2%}")
    print(f"RF slope: {td.ptf_rf_slope:.5}")
    print(f"total updates: {len(tracker_used['ret'])}")
    print(f"Niave: {td.ticker_return.T.mean()['Return']:.2%}")
    print(f"ptf weights (top 10):")
    print((td.weights['Weights']*100).sort_values(ascending=False).head(10))

    x = list()
    y = list()
    for _ in td.tickers:
        x.append(td.ticker_variance[_])
        y.append(td.ticker_return[_])

    pyplot.scatter(tracker_all['var'],tracker_all['ret'],marker='x',color='red')
    pyplot.plot(tracker_used['var'],tracker_used['ret'])
    pyplot.scatter(x,y)
    pyplot.scatter(td.ptf_variance,td.ptf_return)
    pyplot.plot([0,td.ptf_variance],[td.risk_free_rate,td.ptf_return])
    pyplot.show()

    print(td)
    td.save()