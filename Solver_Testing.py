from Backend import PtfDaemon
from pandas import DataFrame, read_csv, concat, array
import numpy as np
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor
from scipy.optimize import minimize, Bounds
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

    def build_point(self):
        "returns (weights, ptf_stdDev, ptf_ret)"
        weights = DataFrame()
        rand_weight = [round(random.random(),4) for _ in range(len(self.tickers))]
        weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]
        weights.index = self.tickers

        var_matr = self.solve_cov_matrix(weights['Weights']).sum().sum()
        
        w = np.array(weights['Weights'].to_list())
        r = np.array(self.ticker_return.T['Return'].to_list())

        return weights['Weights'].to_list(), sqrt(var_matr), sum(w*r)

    def save(self,name='slv_tst'):
        return super().save(name)

    def ptf_return_f(self, params):
        "pass an array of weights"
        r = np.array(self.ticker_return.T['Return'].to_list())
        return sum(r*params)
    
    def ptf_std_f(self,params):
        "pass an array of weights"
        covariance_matrix = self.ticker_data.cov()
        covariance_matrix.index = range(len(covariance_matrix))
        covariance_matrix.columns = covariance_matrix.index

        out = 0.0
        for tick in range(len(params)):
            for tick_ in range(len(params)):
                out += params[tick] * params[tick_] * covariance_matrix[tick][tick_]

        return sqrt(out)

    def minimize_ptf(self):
        w = [1/len(td.tickers) for _ in td.tickers]
        cons = ({'type': 'eq', 'fun': lambda x:  1 - sum(x)})
        res = minimize(td.ptf_std_f, w, bounds=Bounds(lb=0),constraints=cons)
        
        return res.x

if __name__ == '__main__':
    td = solver_testing()

    spy = read_csv('spy.csv')['Symbol']
    for tick in spy[:10]:
        td.add_ticker(tick)

    td.download_data()
    td.calc_beta()
    td.calc_returns()
    td.calc_variance()

    res = td.minimize_ptf()

    ticks_x = list()
    ticks_y = list()
    for tick in td.tickers:
        ticks_x.append(sqrt(td.ticker_variance[tick]['Variance']))
        ticks_y.append(td.ticker_return[tick]['Return'])

    pyplot.scatter(ticks_x,ticks_y)
    pyplot.scatter(td.ptf_std_f(res),td.ptf_return_f(res))
    pyplot.show()