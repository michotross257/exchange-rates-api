import requests
import sqlite3
import datetime
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt


parser = argparse.ArgumentParser(description='Acquire query parameters for call to API.')
parser.add_argument('-b', '--base', default='USD', metavar='',
                    help='Base currency (default: USD).')
parser.add_argument('-s', '--start', default=datetime.datetime(year=2019, month=5, day=1).date(), metavar='',
                    help='Start date of exchange rates history query. Form of date should be YYYY-MM-DD (default: 2019-05-01).')
parser.add_argument('-e', '--end', default=datetime.datetime.now().date(), metavar='',
                    help="End date of exchange rates history query. Form of date should be YYYY-MM-DD (default: Today's date).")
parser.add_argument('-c', '--countries', default='USD,CAD', metavar='',
                    help='Comma separated list of countries to include the comparative exchange plot (Default: USD,CAD).')
parser.add_argument('-r', '--repopulate', action='store_true',
                    help='Whether to repopulate the table from the start date up to and including the end date.')
parser.add_argument('-p', '--plot', action='store_true',
                    help='Whether to include a plot of comparative exchange rates.')
parser.add_argument('-u', '--update', action='store_true',
                    help='Whether to run the daily update code (NOTE: this code will run indefinitely).')
args = parser.parse_args()


def check_for_error(func):
    '''
    Decorator to check whether the API call returned an error. If an error is returned, raise an exception.
    '''
    def api_call(date):
        rsp = func(date)
        if 'error' in rsp:
            raise Exception(rsp['error'])
        return rsp
    return api_call


@check_for_error
def get_api_response(date):
    '''
    Call the stock exchange API and return the decoded response.
    
    Parameters:
        date (datetime.datetime.date): Date used to query API

    Returns:
        dict: Decoded API response
    '''
    rsp = requests.get('https://api.exchangeratesapi.io/{}?base={}'.format(date.strftime('%Y-%m-%d'), args.base))
    return json.loads(rsp.content.decode())


def get_insert_statement_and_values(response, date):
    '''
    Accumulate the INSERT statement and values. Return the statement and values as a tuple.
    
    Parameters:
        response (dict): Single date API response
        date(str): Date to be included in insert statement in format '%Y-%m-%d'

    Returns:
        tuple: INSERT statement (str) and the associated values (tuple)
    '''
    statement = 'INSERT INTO {} VALUES (?,?,'.format(TABLE_NAME) + '?,'*(len(response['rates'])-1)
    statement += '?)'
    values = tuple([date, response['base']] + [response['rates'][x] for x in rate_keys])
    return (statement, values)


def insert_into_table(statement, values):
    '''
    Insert the values into the table.
    
    Parameters:
        statement (str): INSERT statement to be committed
        values(tuple): Values to be included in INSERT statement

    Returns:
        None
    '''
    print('Values to be inserted: {}\n'.format(tuple(zip(table_keys, values))))
    try:
        c.execute(statement, values)
    except sqlite3.IntegrityError:
        pass


TABLE_NAME = 'exchange_rates'
# check to see if the user provided a start and/or end date
# start & current date (start date is a reference; current date will be incremented)
if isinstance(args.start, str):
    year, month, day = args.start.split('-')
    start_date = datetime.datetime(year=int(year), month=int(month), day=int(day)).date()
else:
    start_date = args.start
current_date = start_date
# end date
if isinstance(args.end, str):
    year, month, day = args.start.split('-')
    today_date = datetime.datetime(year=int(year), month=int(month), day=int(day)).date()
else:
    today_date = args.end

days = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday'
]
# numerical values associated with day names
# see help(datetime.datetime.isoweekday)
isoweekdays = dict(zip(range(1,8), days))

# request data from the API
response = get_api_response(current_date)
# the country IDs
rate_keys = list(response['rates'].keys())
# the full list of table column names
table_keys = ['date', 'base'] + rate_keys

# check to make sure the countries (if user provided) are valid
countries = [x.strip() for x in args.countries.split(',')]
set_diff = set(countries).difference(set(rate_keys))
msg = 'The following currencies provided are not valid: {}.\nList of valid currencies: {}'.format(set_diff,
                                                                                                  rate_keys)
assert not len(set_diff), msg

# generate the CREATE TABLE statement
create_table_statement = 'CREATE TABLE IF NOT EXISTS {} ('.format(TABLE_NAME)
create_table_statement += '\n\tdate text PRIMARY KEY,\n\tbase text,'
for cnt, value in enumerate(rate_keys):
    comma = '' if cnt == len(response['rates'])-1 else ','
    create_table_statement = create_table_statement + '\n\t{} real{}'.format(value, comma)
create_table_statement += '\n)'

# create the database and connect to it
with sqlite3.connect('exchange_rate.db') as conn:
    c = conn.cursor()
    
    # check to see if table exists for plotting in case the user does not choose to repopulate
    # the table but chooses to plot, in which case, raise an exception
    c.execute('SELECT name FROM sqlite_master WHERE name="{}"'.format(TABLE_NAME))
    table_exists = len(c.fetchall())
    
    if args.repopulate:
        # create the table (if it doesn't exist)
        c.execute(create_table_statement)
        # accumulate all of the data from start date up to and including today
        while current_date <= today_date:
            # if not a weekend, then request updated exchange rates
            if isoweekdays[current_date.isoweekday()] not in ['Saturday', 'Sunday']:
                response = get_api_response(current_date)
            statement, values = get_insert_statement_and_values(response, current_date.strftime('%Y-%m-%d'))
            insert_into_table(statement, values)
            # add a day to the current date
            current_date += datetime.timedelta(1)
    
    # ====================   
    # CREATE VISUALIZATION
    # ====================
    if args.plot:
        if not table_exists:
            msg = 'The table "{}" is not populated. Include the -p flag to populate the table before plotting.'.format(TABLE_NAME)
            raise Exception(msg)
        if args.base not in countries:
            countries.append(args.base)
        select_statement = 'SELECT ' + '{},'*len(countries)
        select_statement = select_statement.rstrip(',').format(*countries) + '\nFROM {};'.format(TABLE_NAME)
        c.execute(select_statement)
        data = c.fetchall()
        # isolate rates
        rates = {}
        for index, country in enumerate(countries):
            rates[country] = [x[index] for x in data]

        # get the xticklabels (i.e. dates)
        # difference in days between today and start date
        time_diff = today_date - start_date
        # get the dates from start to today
        dates = [(start_date + datetime.timedelta(x)) for x in range(1, time_diff.days+1)]
        indexes = np.linspace(0, len(dates)-1, 8).astype(int)
        xticklabels = [dates[index] for index in indexes]

        # graph the data
        fig, ax = plt.subplots(figsize=(16,6))
        for r in rates:
            plt.plot(rates[r], label=r)
        ax.set_xticklabels(xticklabels)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Exchange Rate', fontsize=12)
        non_base_currencies = list(rates.keys())
        non_base_currencies.remove(args.base)
        title = 'Exchange Rate for ' + '{}, '*(len(rates)-1)
        title = title.rstrip(', ').format(*non_base_currencies) + '\nWhen Base Rate is {} Currency'.format(args.base)
        plt.title(title, fontsize=18)
        plt.legend()
        plt.show()
    
    
    if args.update:
        # loop to run indefinitely to gather daily update
        # determine the next day. When it arrives, we need to call the API
        next_day = today_date + datetime.timedelta(1)
        while True:
            today_date = datetime.datetime.now().date()
            # if tomorrow has arrived...
            if today_date == next_day:
                response = get_api_response(today_date)
                statement, values = get_insert_statement_and_values(response, current_date.strftime('%Y-%m-%d'))
                insert_into_table(statement, values)
                next_day = today_date + datetime.timedelta(1)
