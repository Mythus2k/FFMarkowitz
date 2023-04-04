from Backend import PtfDaemon
from pandas import DataFrame, concat
from numpy import array
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

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
        weights = DataFrame()
        sgd = make_pipeline(StandardScaler(),SGDRegressor())
        
        weights['Weights'] = [1/len(self.tickers) for _ in self.tickers]
        weights.index = self.tickers
        covariance = self.solve_cov_matrix(weights['Weights']).sum()
        y = (self.ticker_return.T['Return'] * weights['Weights']).to_list()
        for t in covariance.index:
            covariance[t] = sqrt(covariance[t])
        x = covariance.to_list()

        y = array(y).reshape(1,-1)
        x = array(x).reshape(1,-1)

        print(x)
        print()
        print(y)
        exit()

        sgd.fit(x,y)
        

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