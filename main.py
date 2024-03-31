import configparser
import datetime
import logging
from tkinter.scrolledtext import ScrolledText
from tkinter import (DISABLED, END, Entry, INSERT, NORMAL, Button, Label, StringVar, Tk, mainloop, ttk, NO, Toplevel, messagebox)
from threading import Thread
import os
import time

import mysql.connector as connector


def create_log():
    logging.basicConfig(filename='company_manager/system_log.log', filemode='a', format="%(asctime)s: %(levelname)s - %(message)s\n", datefmt='%d-%m-%y %H:%M', level=logging.INFO)

create_log()
logger = logging.getLogger()
logger.info("Program started")

file_path = 'company_manager/system_settings.ini'

# global parameters and settings related functions

def get_log(text_field):

    text_field.config(state=NORMAL)
    text_field.delete('1.0', END)

    log_path = 'company_manager/system_log.log'
    with open(log_path, 'r') as file:
        content = reversed(file.readlines())
        for x in content:
            logged_content.set(x)
            text_field.insert(INSERT, logged_content.get())
    
    text_field.config(state=DISABLED)


def create_settings():
    try:
        with open(file_path, 'r') as file:
            logger.info('Settings file found.')

    except Exception as e:
        logger.warning(f"{e}; Settings file not found. Creating new one...")
        with open(file_path, 'w') as file:
            file.write("[CONNECTION]\n")
            file.write("host = host address\n")
            file.write("port = port\n")
            file.write("user = user\n")
            file.write("password = connection password\n")
            file.write("database = database name")


def load_settings():
    try:
        connection_settings_parse = configparser.ConfigParser()
        connection_settings_parse.read(file_path)
            
        set_host = connection_settings_parse['CONNECTION']['host']
        set_port = connection_settings_parse['CONNECTION']['port']
        set_user = connection_settings_parse['CONNECTION']['user']
        set_password = connection_settings_parse['CONNECTION']['password']
        set_database = connection_settings_parse['CONNECTION']['database']

        connection_settings = [set_host, set_port, set_user, set_password, set_database]
        return [connection_settings]

    except Exception as e:
        logger.error("Couldn't load settings file... Possibly due to wrong configuration structure.")
        logger.warning("Deleting system_settings.ini and creating another one...")
        try:
            os.remove(file_path)
        except:
            pass
        time.sleep(2)
        create_settings()
        logger.info('New settings file created. All default values have been restored.')
        return load_settings()


def new_default_connection():

    try:

        global host_input, port_input, user_input, password_input, database_input
        variables = [host_input.get(), port_input.get(), user_input.get(), password_input.get(), database_input.get()]

        with open(file_path, 'r') as file:
            existing = file.readlines()
            logger.info('Reading existing connection settings...')
            logger.info("Existing: %s"%([x.strip('\n') for x in existing]))
        with open(file_path, 'w') as file:
            for i,x in enumerate(existing, start=-1):
                if '=' in x:
                    new_value = str(x.split('=')[0]+f'= {variables[i]}\n') 
                    logger.warning('Replacing %s with %s'%(x.strip('\n'), new_value.strip('\n')))
                    file.write(new_value)
                else:
                    file.write(x)

    except FileNotFoundError:

        logger.warning('Could not save connections parameters: settings file does not exist...')
        create_settings()
        new_default_connection()


def clear_connection_input():
    global host_input, port_input, user_input, password_input, database_input
    
    for x in [host_input, port_input, user_input, password_input, database_input]:
        x.delete(0, END)


def load_default_parameters():
    settings = load_settings()[0]
    return {
        'host':settings[0],
        'port':settings[1],
        'user':settings[2],
        'password':settings[3],
        'database':settings[4]
    }

# connection related functions

def update_connection_indicators(good=True):
    if good == True:
        connection_status.set(f"Connection established. Host: {host}")
        connection_status_label.configure(text=connection_status.get(), style='connected.TLabel')
        connection_general_indicator.configure(text=f'Connected to {host}.', style='connected2.TLabel')
    else:
        connection_status.set('No connection established')
        connection_status_label.configure(text=connection_status.get(), style='nconnected.TLabel')
        connection_general_indicator.configure(text='Not connected.', style='nconnected2.TLabel')


connection = None
cursor = None

def attempt_connection(use_default_parameters=True):

    global connection, cursor
    global host, port, user, password, database

    if use_default_parameters is True:
        host, port, user, password, database = load_default_parameters().values()

    else:
        host = host_input.get()
        port = port_input.get()
        user = user_input.get()
        password = password_input.get()
        database = database_input.get()

    try:
        if connection != None:
            connection.close()
        connection = connector.connect(
            host = host,
            port = port, 
            user = user, 
            password = password,
            database = database
        )

        cursor = connection.cursor()

    except Exception as e:
        logger.error(f"Exception: {e}. Couldn't connect.")
        update_connection_indicators(good=False)

    else:
        logger.info(f'Connection established. Host: {host}')
        update_connection_indicators()
        create_table(connection, cursor)
        return connection


# db communication related functions

def create_table(connection, cursor):
    global database
    if connection:
        try:
            cursor.execute(f'USE {database}')
            cursor.execute('CREATE TABLE IF NOT EXISTS companies_table (id INTEGER PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100), trade_name VARCHAR(100), request VARCHAR(100), contact VARCHAR(100))')
            connection.commit()
            logger.info(f'Banco de dados {database} encontrado.')
            retrieve_data('companies_table', connection, cursor)
        except Exception as e:
            logger.error(f'{e}')

    else:
        logger.error(f'Could not create companies_table inside database {database}. No connection established.')


def retrieve_data(table, connection, cursor):
    try:
        cursor.execute(f"SELECT * FROM {table}")
        values = cursor.fetchall()
        if values != None:
            for v in values:
                companies_table.insert('', index='end', values=(v[0], v[1], v[3]), iid=v[0])
    except Exception as e:
        logger.error(f'Could not retrieve data from table {table}. {e}')
        create_table(connection, cursor)
    

def raise_connection_error():
    messagebox.showerror(title='Erro', message=f'Erro de conexão...')


def database_insert(connection, cursor, name, trade_name, contact, request='Nenhuma'):
    global companies_table

    try: # arrumar isso aqui: tente gerar varios rapidamente para ver... id's estranhos...
        cursor.execute(f'USE {database}')

        cursor.execute(f"SELECT id FROM companies_table")
        values = cursor.fetchall()
        companies_table.insert(parent='', index='end', values=([len(values)+1, name, request]))

        cursor.execute('INSERT INTO companies_table (name, trade_name, request, contact) VALUES (%s, %s, %s, %s)', [name, trade_name, request, contact])
        connection.commit()
    except:
        raise_connection_error()


def database_remove(connection, cursor):
    global companies_table

    try:
        cursor.execute(f'USE {database}')
        selected_rows = companies_table.selection()
        if len(selected_rows) >= 1:
            try:
                selected_rows = companies_table.selection()
                names = [f'Código: {x[0]} - Razão social: {x[1]}' for x in [companies_table.item(x).get('values') for x in selected_rows]]
                
                if messagebox.askokcancel(title='Aviso', message='As seguintes empresas serão removidas do banco de dados: '+f'\n'.join(names)) == True:
                    for id in [x for x in selected_rows]:
                        print(id)
                        cursor.execute(f'DELETE FROM companies_table WHERE id = {id if "I" not in id else id.strip("I").lstrip("0")}')
                        companies_table.delete(id if "I" not in id else id.strip("I").lstrip("0"))
                    connection.commit()
            except:
                logger.info("Couldn't delete; No rows selected or row doesn't exist")

    except:
        raise_connection_error()

# init function

def initialize():
    global host, port, user, password, database, connection
    attempt_connection(use_default_parameters=True)


# seccondary_windows
    

def company_registration_window():
    window = Toplevel()
    window.geometry('500x500')
    window.title('Novo Cadastro')
    window.resizable(width=False, height=False)

    registration_frame = ttk.Frame(window, width=200, height=100)
    registration_frame.grid(row=1, column=0)

    registration_frame.grid_rowconfigure(1, weight=1)
    registration_frame.grid_rowconfigure(2, weight=1)
    registration_frame.grid_rowconfigure(3, weight=1)

    registration_frame.grid_columnconfigure(1, weight=2)
    registration_frame.grid_columnconfigure(2, weight=2)

    name_label = ttk.Label(registration_frame, text='Razão social')
    name_label.grid(row=1, column=1, sticky='w', padx=5, pady=5)

    name_input = ttk.Entry(registration_frame)
    name_input.grid(row=1, column=2, sticky='w', padx=5, pady=5)

    trade_name_label = ttk.Label(registration_frame, text='Nome fantasia')
    trade_name_label.grid(row=2, column=1, sticky='w', padx=5, pady=5)

    trade_name_input = ttk.Entry(registration_frame)
    trade_name_input.grid(row=2, column=2, sticky='w', padx=5, pady=5)

    contact_label = ttk.Label(registration_frame, text='Resp. contabilidade')
    contact_label.grid(row=3, column=1, sticky='w', padx=5, pady=5)

    contact_input = ttk.Entry(registration_frame)
    contact_input.grid(row=3, column=2)

    register_button = ttk.Button(registration_frame, text='register')
    register_button.configure(command=lambda: database_insert(connection, cursor, str(name_input.get()), str(trade_name_input.get()), str(contact_input.get())))
    register_button.grid(row=4, column=2, sticky='e', padx=5, pady=5)


# Style

root = Tk()

style = ttk.Style()
style.theme_use('default')

colors = {'good':'#218251',
    'bad':'#C41E3D',
    'dark_bg':'#07080A',
    'light_bg':'#101316',
    'inactive_bg':'#141B28',
    'inactive_font':'#586A8E',
    'active_bg':'#334262',
    'active_font':'#849DD1',
    'white_font':'#D6D6D6',
    'highlight_bg':'#2D82B7',
    'nhighlighted':'#1C212D'
}

style.theme_settings('default', {
    'TNotebook.Tab':{
        'configure':{'padding':10, 'borderwidth':0, 'background':colors['inactive_bg'], 'foreground':colors['inactive_font']},
        'map':{
            'background':[
                ('selected', colors['active_bg'])],
            'foreground':[('selected', colors['active_font'])]
        }
    },

    'TNotebook':{
        'configure':{'padding':[0, 10, 0, 0], 'background':colors['light_bg'], 'borderwidth':0},
        },

    'TFrame': {
        'configure':{'background':colors['dark_bg'],
        }
    },

    'separator.TSeparator':{
        'configure': {
            'background':colors['active_bg']
        }
    },

    'general_text.TLabel':{
        'configure':{
            'background':colors['dark_bg'], 'foreground':colors['white_font']
        }
    },

    'connection_entry.TEntry':{
        'configure':{
            'fieldbackground':colors['light_bg'], 'foreground':colors['white_font'],
            'borderwidth':0, 'padding':[10, 10, 10, 10]
        }
    }
})


style.layout("Tab", [('Notebook.tab', {'sticky': 'nswe', 'children':
   [('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children':
      [('Notebook.label', {'side': 'top', 'sticky': ''})],
   })],
})]
)

style.configure(
    'connected.TLabel', foreground=colors['white_font'],
    background=colors['good'],
    padding=[390, 10, 415, 10]
)

style.configure(
    'nconnected.TLabel', foreground=colors['white_font'],
    background=colors['bad'],
    padding=[415, 10, 445, 10]     
)

style.configure(
    'connected2.TLabel', foreground=colors['white_font'],
    background=colors['good'],
    padding=[14.5, 15, 10, 15]
)

style.configure(
    'nconnected2.TLabel', foreground=colors['white_font'],
    background=colors['bad'],
    padding=[33, 15, 33, 15]     
)

style.configure(
    'title.TLabel', foreground=colors['white_font'], background=colors['dark_bg'],
    font=('', 12)
)


style.configure('main_button.TButton',
    background=colors['active_bg'], foreground=colors['active_font'],
    focuscolor=colors['active_bg'], relief='solid', borderwidth=0
)

style.map('main_button.TButton', background=[('active', '#404E6C')], 
    focuscolor=[('active', '#404E6C')]
)

style.configure('seccondary_button.TButton', background=colors['nhighlighted'], foreground=colors['inactive_font'],
    focuscolor=colors['nhighlighted'], relief='solid', borderwidth=0
)

style.configure('delete_log.TButton',
    background=colors['bad'], foreground=colors['white_font'],
    focuscolor=colors['bad'], relief='solid', borderwidth=0
)

style.map('delete_log.TButton', background=[('active', '#89162D')], 
    focuscolor=[('active', '#89162D')]
)

style.map('seccondary_button.TButton', background=[('active', colors['inactive_bg'])])


# Root structure

root.title(f'Company Data Manager')
root.geometry('1000x650')
root.resizable(width=False, height=False)
root.configure(bg=colors['light_bg'])

tab_controller = ttk.Notebook(root, height=700, width=1200)
tab_controller.config()
connect_tab = ttk.Frame(tab_controller)
main_tab = ttk.Frame(tab_controller)
settings_tab = ttk.Frame(tab_controller)
log_tab = ttk.Frame(tab_controller)

tab_controller.add(main_tab, text='Clients')
tab_controller.add(connect_tab, text='Connections')
tab_controller.add(settings_tab, text='Settings')
tab_controller.add(log_tab, text='Log')
tab_controller.place(x=0, y=2)

connection_status = StringVar()

connection_status_label = ttk.Label(connect_tab, style='connection_label.TLabel')
connection_status_label.place(x=0, y=566)

connection_general_indicator = ttk.Label(root)
connection_general_indicator.place(x=850, y=0)

# Main panel

companies_table = ttk.Treeview(main_tab)

companies_table['columns'] = ('id', 'name', 'request')

companies_table.configure(height=20)

companies_table.column('#0', width=0, stretch=NO)
companies_table.column('id', width=50)
companies_table.column('name', width=400)
companies_table.column('request', width=200)

companies_table.heading('id', text='Code', anchor='center')
companies_table.heading('name', text='Name', anchor='w')
companies_table.heading('request', text='Active Requests', anchor='center')

companies_table.place(x=20, y=40)

search_value = StringVar()

search_bar = ttk.Entry(main_tab)
search_bar.config(style='connection_entry.TEntry')
search_bar.place(x=30, y=500)

search_button = ttk.Button(main_tab, text='search')
search_button.config()
search_button.place(x=200, y=500)

new_company = ttk.Button(main_tab, text='register new company')
new_company.config(command=company_registration_window)
new_company.place(x=400, y=500)

delete_company = ttk.Button(main_tab, text='delete company')
delete_company.config(command=lambda: database_remove(connection, cursor))
delete_company.place(x=600, y=500)

# Connections Panel

settings = load_settings()[0]

entry_host = StringVar(value=settings[0])
entry_port = StringVar(value=settings[1])
entry_user = StringVar(value=settings[2])
entry_password = StringVar(value=settings[3])
entry_database = StringVar(value=settings[4])

connect_tab.grid_columnconfigure(0, weight=1)
connect_tab.grid_rowconfigure(2, weight=15)
connect_tab.grid_rowconfigure(1, weight=0)

setup_frame = ttk.Frame(connect_tab, padding=0, style='connection_frame.TFrame')
setup_frame.place(anchor='center', x=500, y=300)

connection_desc = ttk.Label(connect_tab, text='Connection Setup', style='title.TLabel')
connection_desc.place(x=306, y=98)

sep1 = ttk.Separator(connect_tab, orient='horizontal', style='separator.TSeparator')
sep1.place(x=308, y=130, relwidth=0.383, relheight=0.0045)

host_label = ttk.Label(setup_frame, text='Host', style='general_text.TLabel')
host_input = ttk.Entry(setup_frame, textvariable=entry_host, style='connection_entry.TEntry')
host_label.grid(column=1, row=20, padx=10, sticky='w')
host_input.grid(column=3, row=20, pady=10)

port_label = ttk.Label(setup_frame, text='Port', style='general_text.TLabel')
port_input = ttk.Entry(setup_frame, textvariable=entry_port, style='connection_entry.TEntry')
port_label.grid(column=1, row=40, padx=10, sticky='w')
port_input.grid(column=3, row=40, pady=10)

user_label = ttk.Label(setup_frame, text='User', style='general_text.TLabel')
user_input = ttk.Entry(setup_frame, textvariable=entry_user, style='connection_entry.TEntry')
user_label.grid(column=1, row=60, padx=10, sticky='w')
user_input.grid(column=3, row=60, pady=10)

password_label = ttk.Label(setup_frame, text='Connection Password', style='general_text.TLabel')
password_input = ttk.Entry(setup_frame, textvariable=entry_password, style='connection_entry.TEntry')
password_label.grid(column=1, row=80, padx=10, sticky='w')
password_input.grid(column=3, row=80, pady=10)

database_label = ttk.Label(setup_frame, text='Database to Connect to', style='general_text.TLabel')
database_input = ttk.Entry(setup_frame, textvariable=entry_database, style='connection_entry.TEntry')
database_label.grid(column=1, row=100, padx=10)
database_input.grid(column=3, row=100, pady=10, padx=10)

clear_button = ttk.Button(setup_frame, text='Clear', padding=10, command=clear_connection_input, style='seccondary_button.TButton')
connect_button = ttk.Button(setup_frame, text='Connect', padding=10, command=lambda: Thread(target=attempt_connection, args=(False,), daemon=True).start())
connect_button.configure(style='main_button.TButton')
save_as_default_button = ttk.Button(setup_frame, text='Save as default', padding=10, command=new_default_connection, style='seccondary_button.TButton')

save_as_default_button.grid(column=1, row=200, pady=10, padx=10,  sticky='we')
clear_button.grid(column=2, row=200, pady=10, padx=10, sticky='we')
connect_button.grid(column=3, row=200, pady=10, padx=10,  sticky='we')


# Logging panel

logged_content = StringVar()

logger_desc = ttk.Label(log_tab, text='System Event Logger', style='title.TLabel').place(x=10, y=20)

logger_frame = ttk.Frame(log_tab, relief='solid', padding=15, style='connection_frame.TFrame')
logger_frame.place(x=0, y=75)
logger_frame.grid_rowconfigure(0, weight=0, pad=10)
logger_frame.grid_columnconfigure(0, weight=0)

logging_space = ScrolledText(logger_frame)
logging_space.configure(height=30, width=125, relief='solid', font=('arial', 8))
logging_space.grid(column=0, row=1)
logging_space.config(state=DISABLED, padx=2, fg=colors['white_font'], bg=colors['light_bg'])

get_log_button = ttk.Button(log_tab, command=lambda: get_log(logging_space), style='main_button.TButton')
get_log_button.config(text='Load log', width=20, padding=20)
get_log_button.place(x=810, y=230)

delete_log_button = ttk.Button(log_tab, text='Delete log file', padding=[20, 5, 20, 5], width=20, style='delete_log.TButton')
delete_log_button.place(x=810, y=295)

initialize()

root.mainloop()

