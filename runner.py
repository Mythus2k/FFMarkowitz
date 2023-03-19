from yfinance import download as yfdown
from pandas import read_csv, DataFrame, Timestamp, concat
from pickle import load, dump
from sklearn.linear_model import LinearRegression
# from matplotlib import pyplot
from math import sqrt

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

    def build_ptf(self):
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
  

    def save(self):
        dump(self,open('./Conf/markowitz.conf','wb'))


# if __name__ == '__main__':
#     m = Markowitz_Deamon()

#     m.set_index('vti')
#     m.set_riskfree('^IRX')
#     m.add_tick('tsla')
#     m.add_tick('v')
#     m.add_tick('xom')
#     m.add_tick('meta')
#     m.add_tick('bac')

#     m.build_ptf()
#     print(m.ptf)
#     m.ptf_x = m.efficient['std'][0]
#     m.ptf_y = (100*m.ptf_x)/m.efficient['std'][0]
#     m.save()

#     # GUI for Markowitz solver

import dearpygui.dearpygui as dpg

m = load(open('./Conf/markowitz.conf','rb'))

dpg.create_context()

# ======= Input Items ========
def configure_Itable():
    dt = m.td.index['date']
    dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

    dpg.configure_item('Itick',default_value=f'{m.td.index["ticker"]}')
    dpg.configure_item('Rtick',default_value=f'{m.td.index["return"]:.2%}')
    dpg.configure_item('Stick',default_value=f'{m.td.index["std"]:.2%}')
    dpg.configure_item('Dtick',default_value=f'{dt}')

def build_Itable():
    "Builds Index table in GUI"
    dpg.add_input_text(label='Set Index',tag='set_index',
                       callback = set_index, on_enter=True,
                       width= 55,hint='ticker')
    
    with dpg.table(header_row=True,policy=dpg.mvTable_SizingStretchProp,
            borders_innerV=True, borders_outerV=True, borders_outerH=True):
        dpg.add_table_column(label='Index',width=10)
        dpg.add_table_column(label='Annual Return')
        dpg.add_table_column(label='std deviation')
        dpg.add_table_column(label='last update')
        
        dt = m.td.index['date']
        dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

        with dpg.table_row():
            dpg.add_text(tag='Itick',default_value=f'{m.td.index["ticker"]}')
            dpg.add_text(tag='Rtick',default_value=f'{m.td.index["return"]:.2%}')
            dpg.add_text(tag='Stick',default_value=f'{m.td.index["std"]:.2%}')
            dpg.add_text(tag='Dtick',default_value=f'{dt}')

def set_index(sender, app_data):
    m.set_index(app_data)
    dpg.configure_item('set_index')
    configure_Itable()

def default_Ttext(ticker):
    if ticker == '^IRX':
        return '13 week'
    if ticker == '^FVX':
        return ' 5 year'
    if ticker == '^TNX':
        return '10 year'
    if ticker == '^TYX':
        return '30 year'
    
def build_Ttable():
    "Builds treasury table in GUI"
    dpg.add_combo(items=('13 week',' 5 year','10 year','30 year'),label='Set treasury',
                  tag='set_treasury',default_value=default_Ttext(m.rfd['ticker']), callback = set_treasury,width=75)
    
    with dpg.table(header_row=True, policy=dpg.mvTable_SizingStretchProp,
            borders_innerV=True, borders_outerV=True, borders_outerH=True):
        dpg.add_table_column(label='Rate')
        dpg.add_table_column(label='last update')
        
        dt = m.rfd['date']
        dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

        with dpg.table_row():
            dpg.add_text(tag='Rtreas',default_value=f'{m.rfd["rate"]:.4%}')
            dpg.add_text(tag='Dtreas',default_value=f'{dt}')

def set_treasury(sender, app_data):
    if app_data == '13 week':
        m.set_riskfree('^IRX')
    if app_data == ' 5 year':
        m.set_riskfree('^FVX')
    if app_data == '10 year':
        m.set_riskfree('^TNX')
    if app_data == '30 year':
        m.set_riskfree('^TYX')

    
    dt = m.rfd['date']
    dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

    dpg.configure_item('Rtreas',default_value=f'{m.rfd["rate"]:.4%}')
    dpg.configure_item('Dtreas',default_value=f'{dt}')

def index_rf_table():
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column()

        # adds section for index info
        with dpg.table_row():
            with dpg.group():
                build_Itable()
        
        # adds section for treasury info
        with dpg.table_row():
            with dpg.group():
                build_Ttable()
        
        with dpg.table_row():
            dpg.add_checkbox(label='leveraging',show=False)

# ======= Ticker Items ========
def add_tick(sender, app_data):
    if len(m.td.tickers.loc[m.td.tickers['ticker'] == app_data]) > 0:
        print('already in list - cannot add twice')
        return
    
    m.add_tick(app_data)
    stk = m.td.tickers.loc[m.td.tickers['ticker'] == app_data].reset_index().iloc[0]

    dt = stk['last_update']
    dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

    with dpg.table_row(tag=f"{stk['ticker']}-row",parent='ticker_table'):
        dpg.add_text(tag=f"{stk['ticker']}-ticker",default_value=(f'{stk["ticker"]}').upper())
        dpg.add_text(tag=f"{stk['ticker']}-beta",default_value=f'{stk["beta"]:.2}')
        dpg.add_text(tag=f"{stk['ticker']}-last_update",default_value=f'{dt}')
        dpg.add_button(tag=f"{stk['ticker']}-delete",label='delete',callback=del_tick,user_data=f"{stk['ticker']}")

def del_tick(sender, app_data, user_data):    
    m.del_tick(user_data)
    dpg.delete_item((f"{user_data}").lower()+"-row")

def ticker_table():
    with dpg.group():
        dpg.add_input_text(label='Add tick',tag='add_ticker',
                    callback=add_tick, on_enter=True,
                    width=55,hint='ticker')

        with dpg.table(tag='ticker_table',header_row=True,policy=dpg.mvTable_SizingStretchProp,
                        scrollY=True,height=180,freeze_rows=1):
            cols = ['ticker','beta','last_update','Delete']
            for c in cols:
                dpg.add_table_column(label=c)
            

            for i in iter(m.td.tickers.index):
                stk = m.td.tickers.iloc[i]
                dt = stk['last_update']
                dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

                with dpg.table_row(tag=f"{stk['ticker']}-row"):
                    dpg.add_text(tag=f"{stk['ticker']}-ticker",default_value=(f'{stk["ticker"]}').upper())
                    dpg.add_text(tag=f"{stk['ticker']}-beta",default_value=f'{stk["beta"]:.2}')
                    dpg.add_text(tag=f"{stk['ticker']}-last_update",default_value=f'{dt}')
                    dpg.add_button(tag=f"{stk['ticker']}-delete",label='delete',callback=del_tick,user_data=f"{stk['ticker']}")

# ======= Ptf Data ===========
def del_ptf_rows():
    for r in m.ptf['ticks']:
        dpg.delete_item(f"{r}-weight_row")

def build_ptf_rows():
    for r in m.ptf['ticks']:
        with dpg.table_row(tag=f"{r}-weight_row",parent='ptf_data_table'):
            dpg.add_text(f"{r}".upper())
            dpg.add_text(f"{m.ptf['ticks'][r]:.2%}")
            dpg.add_text(f"Not ready")

def ptf_data():
    with dpg.group():
        # builds the weights table
        with dpg.table(header_row=True,scrollY=True,height=180,freeze_rows=1,tag='ptf_data_table'):
            cols = ['Ticker','Weight','Dollars']
            for c in cols:
                dpg.add_table_column(label=f"{c}",tag=f"{c}-column")
            
            build_ptf_rows()

        # build return information
        with dpg.table(header_row=False):
            dpg.add_table_column()
            dpg.add_table_column()

            with dpg.table_row():
                dpg.add_text('E(r)')
                dpg.add_text(f"{m.ptf_y:.2%}",tag='ptf_ret')

            with dpg.table_row():
                dpg.add_text('Std dev')
                dpg.add_text(f"{m.ptf_x:.2%}",tag='ptf_std')

            with dpg.table_row():
                dpg.add_text('E(r)-(1)std')
                dpg.add_text(f"{m.ptf_y-m.ptf_x:.2%}",tag='min_ret')

            with dpg.table_row():
                dpg.add_text('Beta')
                dpg.add_text(f"{m.ptf['beta']:.2}")

# ======= Efficient Frontier =======
def build_ptf():
    del_ptf_rows()
    m.build_ptf()
    dpg.configure_item('eff_front',x=m.perform['std'].to_list(),y=m.perform['er'].to_list())
    x_axis, y_axis = efficient_line()
    dpg.configure_item('risk_line',x=x_axis,y=y_axis)
    plot_point(None,dpg.get_value('risk_level'))
    build_ptf_rows()

def efficient_line():
    x_axis = list()
    y_axis = list()
    for x in range(0,int(m.efficient['std']*1.5*1000)):
        x_axis.append(x/1000)
    for x in iter(x_axis):
        y_axis.append(m.efficient['slope'][0]*x + m.rf)

    return x_axis, y_axis

def plot_point(sender, app_data):
    x_value = m.efficient['std'][0]*(app_data/100)

    m.ptf_x = x_value
    m.ptf_y = (m.efficient['slope'][0]*x_value + m.rf)

    dpg.configure_item('ptf_ret',default_value=f"{m.ptf_y:.2%}")
    dpg.configure_item('ptf_std',default_value=f"{m.ptf_x:.2%}")
    dpg.configure_item('min_ret',default_value=f"{m.ptf_y-m.ptf_x:.2%}")

    dpg.configure_item('desired_risk_point',x=m.ptf_x,y=m.ptf_y)

def frontier_graph():
    with dpg.table(tag='build_ptf-table',header_row=False,policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row(tag='build_ptf-row'):
            dpg.add_button(label='Build Portfolio',callback=build_ptf,width=120)

            dpg.add_slider_float(label='Risk level',tag='risk_level',width=160,callback=plot_point,default_value=(100*m.ptf_x)/m.efficient['std'][0])

    with dpg.plot(label="Efficient Frontier", height=320, width=420):
        # REQUIRED: create x and y axes
        dpg.add_plot_axis(dpg.mvXAxis, label="std")
        dpg.add_plot_axis(dpg.mvYAxis, label="E(r)", tag="y_axis")

        # series belong to a y axis
        dpg.add_line_series((m.perform['std']).to_list(), (m.perform['er']).to_list(), label="Efficient Frontier", parent="y_axis",tag='eff_front')

        x_axis, y_axis = efficient_line()
        dpg.add_line_series(x=x_axis,y=y_axis,label="risk adjuster",parent="y_axis",tag='risk_line')


        # no longer need to comment this out --- just need to run program, adjust slider, and rerun!
        dpg.add_scatter_series(x=m.ptf_x,y=m.ptf_y,label='desired risk point',parent='y_axis',tag='desired_risk_point')

# ======== GUI building ========
with dpg.window(tag='Primary Window'):
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column(label='inputs')
        dpg.add_table_column(label='tickers')
        
        with dpg.table_row():
            with dpg.group():

                # adds section to update index and risk free inputs
                index_rf_table()

                # spacer for visual appeal
                dpg.add_spacer(height=20)

                # adds graph and stuff to update ptf
                frontier_graph()

            # add section to manipulate tickers in portfolio
            with dpg.group():
                # adds table of tickers that can add/del
                ticker_table()

                # add spacer for visual appeal
                dpg.add_input_float(label='Investment',tag='ptf_investment',default_value=m.investing,step=100,step_fast=1_000,min_value=0,format='%.2f')

                # add ptf data to gui
                ptf_data()


dpg.create_viewport(title='Markowitz Portfolio Solver', width=720, height=600)

dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_primary_window('Primary Window',True)

dpg.start_dearpygui()
m.save()
dpg.destroy_context()
