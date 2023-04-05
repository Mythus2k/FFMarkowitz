from Backend import PtfDaemon
from Solver_Testing import solver_testing
import dearpygui.dearpygui as dpg
from pickle import load
from math import sqrt
from pandas import DataFrame

# td = load(open('./Conf/ptf_Daemon.conf','rb'))
td = load(open('./Conf/slv_tst.conf','rb'))
print(td)

dpg.create_context()

# ======== change period, interval, OHLC
def set_ohlc(sender, app_data):
    td.ohlc = app_data

def ohlc_window():
    dpg.add_combo(items = ['Open','High','Low','Close','Adj Close'],
                label = 'OHLC options',
                tag = 'ohlc_combo',
                callback = set_ohlc,
                default_value= td.ohlc,
                width = 90)

def set_period(sender, app_data):
    td.period = app_data

def period_window():
    dpg.add_combo(items = ['10y','5y','2y','1y','ytd','6mo','3mo','1mo','5d','1d'],
                label = 'Period options',
                tag = 'period_combo',
                callback = set_period,
                default_value= td.period,
                width = 50)

def set_interval(sender, app_data):
    td.interval = app_data

def interval_window():    
    dpg.add_combo(items = ['3mo','1mo','1wk','5d','1d','1h','90m','60m','30m','15m','5m','2m','1m'],
                label = 'Interval options',
                tag = 'interval_combo',
                callback = set_interval,
                default_value= td.interval,
                width = 50)

def inputs_window():
    with dpg.group(label='inputs',tag='inputs_window'):
        ohlc_window()
        period_window()
        interval_window()

# ======== change index
def set_index(sender, app_data):
    td.index = app_data

def index_window():
    with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit):
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row():
            dpg.add_text(default_value='Index:',
                        tag = 'index_text')
            dpg.add_input_text(tag = 'index_input',
                        default_value = td.index,
                        callback = set_index,
                        no_spaces=True,
                        uppercase=True,
                        width = 60)

# ======== change risk free
def set_treasury(sender, app_data):
    if app_data == '13 week':
        td.set_risk_free_rate('^IRX')
    if app_data == ' 5 year':
        td.set_risk_free_rate('^FVX')
    if app_data == '10 year':
        td.set_risk_free_rate('^TNX')
    if app_data == '30 year':
        td.set_risk_free_rate('^TYX')

    dpg.configure_item('treasury_rate', default_value=f"Rate: {td.risk_free_rate:.2%}")

def treasury_default(tick):
    if tick == '^IRX':
        return '13 week'
    if tick == '^FVX':
        return ' 5 year'
    if tick == '^TNX':
        return '10 year'
    if tick == '^TYX':
        return '30 year'

def treasury_window():
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingFixedFit,
                   borders_innerV=True,borders_outerV=False,
                   borders_innerH=False,borders_outerH=False):
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row():
            dpg.add_combo(items = ['13 week',' 5 year','10 year','30 year'],
                      label = 'Treasury period',
                      tag = 'treasury_combo',
                      callback = set_treasury,
                      default_value= treasury_default(td.risk_free),
                      width = 80)
            
            dpg.add_text(default_value = f"Rate: {td.risk_free_rate:.2%}",
                         tag = 'treasury_rate')

# ======== add/delete tickers - show table
def build_ticker_row(tick):
    if tick in td.ticker_beta.columns:
        beta = f"{td.ticker_beta[tick]['Beta']:.2}"
    else: 
        beta = 'N/A'

    if tick in td.ticker_return.columns:
        ret = f"{td.ticker_return[tick]['Return']:.2%}"
    else: 
        ret = 'N/A'

    if tick in td.ticker_variance.columns:
        std = f"{sqrt(td.ticker_variance[tick]['Variance']):.2%}"
    else: 
        std = 'N/A'
    
    with dpg.table_row(tag=f"{tick}-row",parent='ticker_table'):
        dpg.add_text(tag=f"{tick}-ticker",default_value=(f'{tick}').upper())
        dpg.add_text(tag=f"{tick}-beta",default_value=f"{beta}")
        dpg.add_text(tag=f"{tick}-return",default_value=f"{ret}")
        dpg.add_text(tag=f"{tick}-std",default_value=f"{std}")
        dpg.add_button(tag=f"{tick}-delete",label='Delete',callback=delete_ticker,user_data=f"{tick}")

def add_ticker(sender, app_data):
    tick = dpg.get_value('add_ticker_input')
    if tick in td.tickers:
        print(f'Ticker {tick} already in list')
        return
    
    td.add_ticker(tick)
    build_ticker_row(tick)

    dpg.configure_item('add_ticker_input',default_value='',hint='tick')
    
def delete_ticker(sender, app_data, user_data):    
    td.delete_ticker(user_data)
    dpg.delete_item((f"{user_data}").upper()+"-row")
    dpg.delete_item(f'{user_data}-weight_row')

def add_ticker_window():
    with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit):
        dpg.add_table_column()
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row():
            dpg.add_text(default_value='Add ticker:',
                        tag = 'add_ticker_text')
            dpg.add_input_text(tag = 'add_ticker_input',
                        hint = 'tick',
                        callback = add_ticker,
                        no_spaces=True,
                        uppercase=True,
                        width = 60,
                        on_enter=True)
            dpg.add_button(tag = 'add_ticker_button',
                           label='Add',
                           callback = add_ticker)

def ticker_table_window():
    with dpg.table(tag='ticker_table',header_row=True,policy=dpg.mvTable_SizingStretchProp,
                    scrollY=True,height=180,freeze_rows=1,):
        cols = ['Ticker','Beta','Return','Std. Dev.','Delete']
        for c in cols:
            dpg.add_table_column(label=c)
        
        for tick in td.tickers:
            build_ticker_row(tick)

# ======== ticker data calcs

def individual_calc_controller(sender, app_data):
    if sender == 'data_download':
        td.download_data()
    
    if sender == 'ret_calc':
        td.calc_returns()
        for tick in td.tickers:
            dpg.configure_item(f"{tick}-return",default_value=f"{td.ticker_return[tick]['Return']:.2%}")

    if sender == 'beta_calc':
        td.calc_beta()
        for tick in td.tickers:
            dpg.configure_item(f"{tick}-beta",default_value=f"{td.ticker_beta[tick]['Beta']:.2}")

    if sender == 'var_calc':
        td.calc_variance()
        for tick in td.tickers:
            dpg.configure_item(f"{tick}-std",default_value=f"{sqrt(td.ticker_variance[tick]['Variance']):.2%}")

    if sender == 'optimizer_button':
        td.solve()
        # may need to add some other stuff once optimized solutions are added

def individual_calcs():
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingFixedFit):
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row():
            dpg.add_text("     Data:")
            dpg.add_button(label='Download ',
                           tag = 'data_download',
                           callback= individual_calc_controller)

        with dpg.table_row():
            dpg.add_text("  Returns:")
            dpg.add_button(label='Calculate',
                           tag = 'ret_calc',
                           callback= individual_calc_controller)
            
        with dpg.table_row():
            dpg.add_text('     Beta:')
            dpg.add_button(label='Calculate',
                           tag = 'beta_calc',
                           callback= individual_calc_controller)
            
        with dpg.table_row():
            dpg.add_text('Std. Dev.:')
            dpg.add_button(label='Calculate',
                           tag = 'var_calc',
                           callback= individual_calc_controller)
        
        with dpg.table_row(show=False):
            dpg.add_text('    Solve:')
            dpg.add_button(label='Optimize ',
                           tag = 'optimizer_button',
                           callback= individual_calc_controller)

def calc_all_controller():
    td.download_data()
    td.calc_returns()
    td.calc_beta()
    td.calc_variance()
    
    # Scatter of all positions
    dpg.configure_item('ticker_scatter',x=[sqrt(_) for _ in td.ticker_variance.T['Variance']],y=td.ticker_return.T['Return'].to_list())
    
    for tick in td.tickers:
        dpg.configure_item(f"{tick}-return",default_value=f"{td.ticker_return[tick]['Return']:.2%}")
        dpg.configure_item(f"{tick}-beta",default_value=f"{td.ticker_beta[tick]['Beta']:.2}")
        dpg.configure_item(f"{tick}-std",default_value=f"{sqrt(td.ticker_variance[tick]['Variance']):.2%}")

def calc_all():
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingFixedFit):
        dpg.add_table_column()
        dpg.add_table_column()

        with dpg.table_row():
            dpg.add_text('Update data:')
            dpg.add_button(label='Download',
                           tag='calc_all_button',
                           callback=calc_all_controller)

def calculation_window():
    with dpg.child_window(width=250,height=80):
        with dpg.collapsing_header(label='Individual Calculations',
                                   tag = 'individual_calc_collapsing'):
            individual_calcs()
        calc_all()
    
# ======== graph 

def efficient_line():
    x_axis = list()
    y_axis = list()

    for x in [0,(sqrt(td.ptf_variance)*2)]:
        x_axis.append(x)
    for x in iter(x_axis):
        y_axis.append(td.ptf_rf_slope*x + td.risk_free_rate)

    return x_axis, y_axis

def graph_window():
    with dpg.plot(label="Optimizer Graph", height=320, width=420):
        dpg.add_plot_axis(dpg.mvXAxis, label="Standard Deviation")
        dpg.add_plot_axis(dpg.mvYAxis, label="Expected Return", tag="y_axis")

        # Scatter of all positions
        dpg.add_scatter_series(x=[sqrt(_) for _ in td.ticker_variance.T['Variance']],y=td.ticker_return.T['Return'].to_list(),label='tickers',parent='y_axis',tag='ticker_scatter')
        
        # Point for portfolio risk and return
        dpg.add_scatter_series(x=[sqrt(td.ptf_variance)],y=td.ptf_return,label='ptf',parent='y_axis',tag='ptf_scatter')

        # efficient line
        x_series, y_series = efficient_line()
        dpg.add_line_series(x=x_series,y=y_series,label='efficient',parent='y_axis',tag='efficient_line')

        # point along efficient line
        x_value = sqrt(td.ptf_variance) * td.risk_adjuster
        y_value = td.ptf_rf_slope*x_value + td.risk_free_rate
        dpg.add_scatter_series(x=[x_value],y=[y_value],label='risk level',parent='y_axis',tag='risk_level')

# ======== weights and desired return

def weight_row_builder(tick, weight):
    with dpg.table_row(tag= f'{tick}-weight_row',parent='weight_table'):
        dpg.add_text(f"{tick}")
        dpg.add_text(f"{weight:.2%}")

def risk_adjust_calc(sender, app_data):
    # if received from gui -> update ptf Daemon
    if app_data != None:
        td.risk_adjuster = app_data/100
        
        # graph updates
        x_value = sqrt(td.ptf_variance) * td.risk_adjuster
        y_value = td.ptf_rf_slope*x_value + td.risk_free_rate
        dpg.configure_item('risk_level',x = [x_value],y = [y_value])

        # value print updates
        dpg.configure_item('ptf_ret_text',default_value=f"Return: {(td.ptf_return * td.risk_adjuster) + (td.risk_free_rate * (1-td.risk_adjuster)):.2%}")
        dpg.configure_item('ptf_var_text',default_value= f"Std. Dev.: {sqrt(td.ptf_variance) * td.risk_adjuster:.2%}")


    # collect data
    used_weights = td.weights['Weights']
    risk_free = td.risk_adjuster

    # update weights
    used_weights = used_weights * risk_free
    used_weights.T['Trsry'] = 1 - risk_free

    used_weights = used_weights.sort_values(ascending=False)
    # print(used_weights)

    for tick in used_weights.index:
        dpg.delete_item(f'{tick}-weight_row')
        weight_row_builder(tick, used_weights[tick])

def desired_return_slider():
    dpg.add_slider_float(label="Risk adjuster",
                        tag='risk_slider',
                        format='%.2f',
                        callback= risk_adjust_calc,
                        width=120,
                        default_value=td.risk_adjuster*100)
    
    
    # add leveraging options here with input float that links to max value of slider?

def calc_weights_controller():
    # download and update data
    td.download_data()
    td.calc_returns()
    td.calc_variance()
    td.calc_beta()

    # update displays before solving
    for tick in td.tickers:
        dpg.configure_item(f"{tick}-return",default_value=f"{td.ticker_return[tick]['Return']:.2%}")
        dpg.configure_item(f"{tick}-beta",default_value=f"{td.ticker_beta[tick]['Beta']:.2}")
        dpg.configure_item(f"{tick}-std",default_value=f"{sqrt(td.ticker_variance[tick]['Variance']):.2%}")

    dpg.configure_item('ticker_scatter',x=[sqrt(_) for _ in td.ticker_variance.T['Variance']],y=td.ticker_return.T['Return'].to_list())

    td.solve()

    # efficient line
    x_series, y_series = efficient_line()
    dpg.configure_item('efficient_line',x=x_series,y=y_series,label='efficient',parent='y_axis')

    # Point for portfolio risk and return
    dpg.configure_item('ptf_scatter',x=[sqrt(td.ptf_variance)],y=td.ptf_return,label='ptf',parent='y_axis')

    # point along efficient line
    x_value = sqrt(td.ptf_variance) * td.risk_adjuster
    y_value = td.ptf_rf_slope*x_value + td.risk_free_rate
    dpg.configure_item('risk_level',x=[x_value],y=[y_value],label='risk level',parent='y_axis')

    # value print updates
    dpg.configure_item('ptf_ret_text',default_value=f"Return: {(td.ptf_return * td.risk_adjuster) + (td.risk_free_rate * (1-td.risk_adjuster)):.2%}")
    dpg.configure_item('ptf_var_text',default_value= f"Std. Dev.: {sqrt(td.ptf_variance) * td.risk_adjuster:.2%}")

    risk_adjust_calc(None,None)

def calc_weights_button():
    with dpg.group(horizontal=True):
        dpg.add_text('Solve Weights:')
        dpg.add_button(label='Calculate',
                       tag = 'calc_weight_button',
                       callback=calc_weights_controller)

def weight_table_builder():
    with dpg.table(tag='weight_table',header_row=True,policy=dpg.mvTable_SizingFixedFit,
                   freeze_rows=1,height=250,scrollY=True):
        dpg.add_table_column(label='Ticker')
        dpg.add_table_column(label='Weight')

        risk_adjust_calc(None,None)

def output_window():
    with dpg.group():
        with dpg.group(horizontal=False):
            desired_return_slider()
            calc_weights_button()

        weight_table_builder()

# ======= show return, variance, other
def portfolio_values_window():
    with dpg.child_window(width=200,height=80,no_scrollbar=True):
        dpg.add_text(f"Portfolio Results:")
        dpg.add_text(default_value= f"Return: {(td.ptf_return * td.risk_adjuster) + (td.risk_free_rate * (1-td.risk_adjuster)):.2%}",
                     tag='ptf_ret_text')
        dpg.add_text(default_value= f"Std. Dev.: {sqrt(td.ptf_variance) * td.risk_adjuster:.2%}",
                     tag='ptf_var_text')

# ======== Other Gui elements to run
# create viewport
dpg.create_viewport(title='Optimal Portfolio Solver', width=720, height=650,
                    #small_icon=None,large_icon=None,
                    # clear_color=[255,255,255,0],
                    )

# ======== Create window to display

#   Windows:
    # output_window
    # graph_window
    # calculation_window    
    # ticker_table_window   
    # add_ticker_window     
    # treasury_window       
    # index_window          
    # inputs_window         

with dpg.window(tag='Primary Window'):
    with dpg.group(horizontal=True):
        with dpg.group():
            inputs_window()
            treasury_window()
            index_window()
            portfolio_values_window()
            # calculation_window()  # Kinda useless
        with dpg.group():
            add_ticker_window()
            ticker_table_window()
    with dpg.group(horizontal=True):
        graph_window()
        output_window()


# setup and show
dpg.setup_dearpygui()
dpg.show_viewport()

# set viewport
dpg.set_primary_window('Primary Window',True)

# start process
dpg.start_dearpygui()

# Close window
td.save()
dpg.destroy_context()