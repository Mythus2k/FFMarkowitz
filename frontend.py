from Backend import PtfDaemon
import dearpygui.dearpygui as dpg
from pickle import load

td = load(open('./Conf/ptf_Daemon.conf','rb'))
print(td)

dpg.create_context()

# ======== change period, interval, OHLC
# set the ohlc
def set_ohlc(sender, app_data):
    td.ohlc = app_data

# add OHLC options
def ohlc_window():
    dpg.add_combo(items = ['Open','High','Low','Close','Adj Close'],
                label = 'OHLC options',
                tag = 'ohlc_combo',
                callback = set_ohlc,
                default_value= td.ohlc,
                width = 90)

# set the period
def set_period(sender, app_data):
    td.period = app_data

# add period options
def period_window():
    dpg.add_combo(items = ['10y','5y','2y','1y','ytd','6mo','3mo','1mo','5d','1d'],
                label = 'Period options',
                tag = 'period_combo',
                callback = set_period,
                default_value= td.period,
                width = 50)
    
# set the interval
def set_interval(sender, app_data):
    td.interval = app_data

# add interval options
def interval_window():    
    dpg.add_combo(items = ['3mo','1mo','1wk','5d','1d','1h','90m','60m','30m','15m','5m','2m','1m'],
                label = 'Interval options',
                tag = 'interval_combo',
                callback = set_interval,
                default_value= td.interval,
                width = 50)

# create a group for this category
def inputs_window():
    with dpg.group(label='inputs',tag='inputs_window'):
        ohlc_window()
        period_window()
        interval_window()

# ======== change index

# ======== change risk free
# set treasury rate
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

# find the starting treasury
def treasury_default(tick):
    if tick == '^IRX':
        return '13 week'
    if tick == '^FVX':
        return ' 5 year'
    if tick == '^TNX':
        return '10 year'
    if tick == '^TYX':
        return '30 year'

# create the treasury window
def treasury_window():
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingFixedFit,
                   borders_innerV=True,borders_outerV=True,
                   borders_innerH=True,borders_outerH=True):
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

# ======== add tickers

# ======== see and delete tickers

# ======== calculate and include slider for desired return

# ======== graph

# ======== Create window to display
with dpg.window(tag='Primary Window'):
    inputs_window()


# ======== Other Gui elements to run
# create viewport
dpg.create_viewport(title='Optimal Portfolio Solver', width=720, height=600)

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