import cvxpy as cp
import numpy as np
import pandas as pd
import yfinance as yf
from math import sqrt


class TickerDaemon:
    def __init__(self):
        self.tickers = set()
        self.return_data = pd.DataFrame()
        self.std_data = pd.DataFrame()
        self.market_data = pd.DataFrame()

    def add_ticker(self, ticker):
        self.tickers.add(ticker)

    def delete_ticker(self, ticker):
        self.tickers.discard(ticker)

    def clear_tickers(self):
        self.tickers.clear()

    def download_market_data(self, period='10y', interval='1mo', ohlc='Adj Close'):
        data = yf.download(list(self.tickers), period=period, interval=interval).dropna()
        returns = data[ohlc].pct_change()
        if interval == '3mo':
            self.return_data = np.sqrt(4) * returns.mean()
            self.std_data = np.sqrt(4) * returns.std()
        if interval == '1mo':
            self.return_data = np.sqrt(12) * returns.mean()
            self.std_data = np.sqrt(12) * returns.std()
        if interval == '1d':
            self.return_data = np.sqrt(252) * returns.mean()
            self.std_data = np.sqrt(252) * returns.std()

        self.market_data = data[ohlc]
        return data

    def get_ticker_data(self):
        data = pd.concat([self.return_data, self.std_data], axis=1)
        data.columns = ['Return', 'Std']
        data['Market data'] = ([self.market_data[i] for i in self.market_data])
        return data


class MarkowitzDaemon():
    def __init__(self, period='10y', interval='1mo', ohlc='Adj Close') -> None:
        self.td = TickerDaemon()
        self.portfolio_return = float()
        self.portfolio_std = float()
        self.portfolio_weights = dict()

        self.period = period
        self.interval = interval
        self.ohlc = ohlc

    def add_ticker(self, ticker):
        self.td.add_ticker(ticker)

    def delete_ticker(self, ticker):
        self.td.delete_ticker(ticker)

    def download_market_data(self):
        self.td.download_market_data(self.period, self.interval, self.ohlc)

    def solve_efficient(self):
        # get list of tickers from tickerDeamon
        tickers = list(self.td.tickers)

        # Calculate returns
        returns = self.td.market_data.pct_change().dropna()

        # Calculate expected returns and covariance matrix
        mu = returns.mean()
        Sigma = returns.cov()

        # Define optimization variables
        w = cp.Variable(len(tickers))

        # Define optimization problem
        objective = cp.Minimize(cp.quad_form(w, Sigma))
        constraints = [w >= 0, cp.sum(w) == 1]
        problem = cp.Problem(objective, constraints)

        # Solve optimization problem
        problem.solve()

        # Calculate expected return and variance of optimized portfolio
        portfolio_return = mu.dot(w.value)
        portfolio_variance = w.value.T.dot(Sigma).dot(w.value)

        # Clean w.values - some very very small negatives given
        for _ in range(len(w.value)):
            if w.value[_] < 0:
                w.value[_] = 0

        # dict of weights matched to the relevant ticker
        portfolio_weights = dict()
        for _ in range(len(tickers)):
            portfolio_weights[f"{tickers[_]}"] = w.value[_]

        # Print optimized weights, expected return, and variance
        print('Optimized weights:')        
        for _ in range(len(tickers)):
            print(f"{tickers[_]}: {w.value[_]:.2%}")
        print()
        print(f"Expected return: {portfolio_return:.2%}")
        print(f"Std Dev: {sqrt(portfolio_variance):.2%}")

        self.portfolio_return = portfolio_return
        self.portfolio_std = sqrt(portfolio_variance)
        self.portfolio_weights = portfolio_weights

        return portfolio_return, portfolio_variance, portfolio_weights
    

if __name__ == '__main__':
    m = MarkowitzDaemon(period='10y',interval='1mo')

    m.add_ticker('bac')
    m.add_ticker('xom')
    m.add_ticker('tsla')
    m.add_ticker('meta')
    m.add_ticker('msft')
    m.add_ticker('v')

    m.download_market_data()

    m.solve_efficient()