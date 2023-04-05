from Backend import PtfDaemon
from pandas import DataFrame, concat
from numpy import array
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor, LinearRegression
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

    def solve(self):
        pass
        

def build_point():
    weights = DataFrame()
    rand_weight = [round(random.random(),4) for _ in range(len(td.tickers))]
    weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]
    weights.index = td.tickers

    var_matr = td.solve_cov_matrix(weights['Weights']).sum()
    x = [sqrt(_) for _ in var_matr.values]
    
    y = (td.ticker_return.T['Return'] * weights['Weights']).sum()

    return x, y

if __name__ == '__main__':
    td = solver_testing()

    td.add_ticker('xom')
    td.add_ticker('tsla')
    td.add_ticker('meta')
    td.add_ticker('bac')
    td.add_ticker('wfc')

    td.download_data()

    td.calc_returns()
    td.calc_beta()
    td.calc_variance()

    x = []
    y = []

    for _ in range(500):
        out = build_point()
        x.append(out[0])
        y.append(out[1])

    reg = LinearRegression()
    reg.fit(x,y)

    print(reg.coef_)
    print(reg.intercept_)

    x = array(x)
    pyplot.scatter([_.sum() for _ in x],y)
    pyplot.scatter(array(reg.coef_).sum(),reg.intercept_)
    pyplot.show()