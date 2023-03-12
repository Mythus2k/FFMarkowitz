# GUI for Markowitz solver

import dearpygui.dearpygui as dpg
from Markowitz import Markowitz_Deamon, Ticker_Deamon
from pickle import load

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
            dpg.add_text(tag='Rtreas',default_value=f'{m.rfd["rate"]/100:.4%}')
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

    dpg.configure_item('Rtreas',default_value=f'{m.rfd["rate"]/100:.4%}')
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

        with dpg.table(tag='ticker_table',header_row=True,policy=dpg.mvTable_SizingStretchProp):
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

# ======== GUI building ========
with dpg.window(tag='Primary Window'):
    with dpg.table(header_row=False,policy=dpg.mvTable_SizingStretchProp):
        dpg.add_table_column(label='inputs')
        dpg.add_table_column(label='tickers')
        
        with dpg.table_row():
            # adds section to update index and risk free inputs
            index_rf_table()

            # add section to manipulate tickers in portfolio
            ticker_table()


dpg.create_viewport(title='Markowitz Portfolio Solver', width=600, height=600)

dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_primary_window('Primary Window',True)

dpg.start_dearpygui()
m.save()
dpg.destroy_context()
