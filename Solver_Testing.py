from Backend import PtfDaemon
from pandas import DataFrame, read_csv, concat, array
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor
from scipy.optimize import minimize
import random

class solver_testing(PtfDaemon):
    def __init__(self, period = '10y', interval = '1mo', risk_free = '^TNX', ohlc = 'Adj Close') -> None:
        super(PtfDaemon, self).__init__()
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

    def fun(self):
        # (x[0] - 1) ** 2 + (x[1] - 2.5)**2.
        x = [self.ticker_return[tick] for tick in self.tickers]
        
        return array([x[_] * w[_] for _ in range(len(self.tickers))]).sum()

    def solve_weights(self,ptf_builds=400,plot=False):
        weights = DataFrame()
        rand_weight = [round(random.random(),4) for _ in range(len(self.tickers))]
        weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]
        weights.index = self.tickers

        res = minimize(fun, weights['Weights'].to_list())

    def build_point(self):
        weights = DataFrame()
        rand_weight = [round(random.random(),4) for _ in range(len(self.tickers))]
        weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]
        weights.index = self.tickers

        var_matr = self.solve_cov_matrix(weights['Weights']).sum().sum()
        
        x = weights['Weights'].to_list()
        
        y = sqrt(var_matr)

        return x, y

    def solve(self,ptf_builds=400,plot=False):
        self.weights = self.solve_weights(ptf_builds,plot)
        self.ptf_variance = self.solve_cov_matrix(self.weights['Weights']).sum().sum()
        self.ptf_return = (self.ticker_return.T['Return'] * self.weights['Weights']).sum()
        self.ptf_rf_slope = (self.risk_free_rate - self.ptf_return) / (0 - sqrt(self.ptf_variance))

    def save(self,name='slv_tst'):
        return super().save(name)

if __name__ == '__main__':
    td = solver_testing()

    # td.add_ticker('xom')
    # td.add_ticker('tsla')
    # td.add_ticker('meta')
    # td.add_ticker('bac')
    # td.add_ticker('wfc')
    # td.add_ticker('v')
    # td.add_ticker('c')

    spy = read_csv('spy.csv')
    for tick in spy['Symbol'][10:15]:
        td.add_ticker(tick)  

    td.download_data()

    td.calc_returns()
    td.calc_beta()
    td.calc_variance()

    td.solve(ptf_builds=1,plot=True)
    print(td)