# GUI for Markowitz solver

import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

from Markowitz import Markowitz_Deamon
m = Markowitz_Deamon()

dpg.create_context()

def configure_Itable():
    dt = m.td.index['date']
    dt = str(dt.day)+'/'+str(dt.month)+'/'+str(dt.year)

    dpg.configure_item('Itick',default_value=f'{m.td.index["ticker"]}')
    dpg.configure_item('Rtick',default_value=f'{m.td.index["return"]:.2%}')
    dpg.configure_item('Stick',default_value=f'{m.td.index["std"]:.2%}')
    dpg.configure_item('Dtick',default_value=f'{dt}')

def build_Itable():
    with dpg.table(header_row=True,width=305,policy=dpg.mvTable_SizingFixedFit,
            borders_innerV=True, borders_outerV=True, borders_outerH=True):
        dpg.add_table_column(label='Index',width=10)
        dpg.add_table_column(label='Annual Return')
        dpg.add_table_column(label='deviation')
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



with dpg.window(tag='Primary Window'):
    dpg.add_input_text(label='Set Index',tag='set_index',
                       callback = set_index, on_enter=True,
                       width= 55,hint='ticker')

    # adds table for index info
    build_Itable()
    
    


dpg.create_viewport(title='Markowitz Portfolio Solver', width=600, height=600)

# demo.show_demo()

dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_primary_window('Primary Window',True)

dpg.start_dearpygui()
dpg.destroy_context()

