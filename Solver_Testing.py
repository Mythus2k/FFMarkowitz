from Backend import PtfDaemon
from pandas import DataFrame, concat
from numpy import array
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
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

    def rand_weights(self):
        weights = DataFrame()
        rand_weight = [round(random.random(),4) for _ in range(len(self.tickers))]
        weights['Weights'] = [w / sum(rand_weight) for w in rand_weight]       
        weights.index = self.tickers

        return weights

    def spit_std_ret(self):
        weights = self.rand_weights()
        cov = self.solve_cov_matrix(weights['Weights']).sum().sum()
        ret = (self.ticker_return * weights['Weights']).T['Return'].sum()

        return sqrt(cov), ret

    def solve(self):
        # weights = DataFrame()
        sgd = make_pipeline(StandardScaler(),SGDRegressor())
        
        x = list()
        y = list()

        for _ in range(10):
            out = self.spit_std_ret()
            x.append(out[0])
            y.append(out[1])

        x = array(x).reshape(-1,1)
        y = array(y).reshape(-1,1)

        sgd.fit(x,y)
        pred_x = [_/100 for _ in range(100)]
        pred_x = array(pred_x).reshape(-1,1)
        pred_y = sgd.predict(pred_x)

        pyplot.plot(pred_x,pred_y)
        pyplot.scatter(x,y)
        pyplot.show()
        

if __name__ == '__main__':
    td = solver_testing()

    td.add_ticker('c')
    td.add_ticker('bac')
    td.add_ticker('wfc')
    td.add_ticker('pypl')
    td.add_ticker('v')

    td.download_data()
    td.calc_returns()
    td.calc_variance()
    td.calc_beta()

    outs = td.solve()