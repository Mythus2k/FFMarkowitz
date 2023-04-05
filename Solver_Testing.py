from Backend import PtfDaemon
from pandas import DataFrame, read_csv
from math import sqrt
from matplotlib import pyplot
from sklearn.linear_model import SGDRegressor
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

    def solve_weights(self,ptf_builds=400,plot=False):
        x = list()
        y = list()
        for _ in range(ptf_builds):
            out = self.build_point()
            x.append(out[0]) # weights
            y.append(out[1]) # std. dev.

        reg = SGDRegressor(max_iter=100_000)
        reg.fit(x,y)
        
        if plot:
            train_x = list()
            for r in x:
                df = DataFrame({'Weights':r},index=self.tickers)
                train_x.append((self.ticker_return.T['Return'] * df['Weights']).sum())

            pyplot.scatter(y, train_x)

            df = DataFrame({'Weights':[_/reg.coef_.sum() for _ in reg.coef_]},index=self.tickers)
            pyplot.scatter(reg.intercept_, (self.ticker_return.T['Return'] * df['Weights']).sum())
            pyplot.show()

        return DataFrame({'Weights':[_/reg.coef_.sum() for _ in reg.coef_]},index=self.tickers)

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
    for tick in spy['Symbol'][:20]:
        td.add_ticker(tick)  

    td.download_data()

    td.calc_returns()
    td.calc_beta()
    td.calc_variance()

    td.solve(ptf_builds=400,plot=True)

    print(td)

    td.save()