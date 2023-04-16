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

    def solve_weights(self):
        weights = DataFrame()
        rand_weight = [round(random.random(),4) for _ in range(len(self.tickers))]
        weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]
        weights.index = self.tickers

        res = minimize(self.fun, weights['Weights'].to_list())

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

    def solve(self):
        self.weights = self.solve_weights()
        self.ptf_variance = self.solve_cov_matrix(self.weights['Weights']).sum().sum()
        self.ptf_return = (self.ticker_return.T['Return'] * self.weights['Weights']).sum()
        self.ptf_rf_slope = (self.risk_free_rate - self.ptf_return) / (0 - sqrt(self.ptf_variance))

    def save(self,name='slv_tst'):
        return super().save(name)

    def return_func(self, params):
        r = np.array(self.ticker_return.T['Return'].to_list())
        s = 0.0

        for i in range(len(params)):
            s += r[i] * params[i]

        return s
    
    def var_func(self,params):
        covariance_matrix = self.ticker_data.cov()
        covariance_matrix.index = range(len(covariance_matrix))
        covariance_matrix.columns = covariance_matrix.index

        out = 0.0

        for tick in range(len(params)):
            for tick_ in range(len(params)):
                out += params[tick] * params[tick_] * covariance_matrix[tick][tick_]

        return sqrt(out)


if __name__ == '__main__':
    td = solver_testing()

    spy = read_csv('spy.csv')['Symbol']
    for tick in spy[:5]:
        td.add_ticker(tick)

    td.download_data()
    td.calc_beta()
    td.calc_returns()
    td.calc_variance()

    w = [1/len(td.tickers) for _ in td.tickers]

    cons = ({'type': 'eq', 'fun': lambda x:  1 - sum(x)})
    res = minimize(td.var_func, w, bounds=Bounds(lb=0),constraints=cons)
    print(res)

    print(res.x)
    print(w)

    # plot a couple 1000 portfolios
    # ret = array(td.ticker_return.T['Return'].to_list())
    # x = list()
    # y = list()
    # for _ in range(1000):
    #     point = td.build_point()
    #     x.append(point[1])
    #     y.append(point[2])

    # print(len(x))
    # print(len(y))

    # pyplot.scatter(x,y)
    # pyplot.show()