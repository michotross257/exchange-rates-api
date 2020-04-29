import argparse
import calendar
from datetime import datetime, timedelta
import json
import requests
import sqlite3
import sys
import warnings

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm


def check_date_arg(dt):
    """
    Helper function to check to see if the user provided a start/end date.

    Args:
        dt(str|datetime.datetime.date): start or end date of query

    Returns:
        datetime.datetime.date: start or end date
    """
    if isinstance(dt, str):
        year, month, day = dt.split('-')
        return datetime(year=int(year), month=int(month), day=int(day)).date()
    return dt


def extract_dates(start, end):
    """
    Extract start and end dates from the argparse values and ensure that the
    end date is greater than the start date.

    Args:
        start(str|datetime.datetime.date): start date of query
        end(str|datetime.datetime.date): end date of query

    Returns:
        tuple: start date and end date
    """
    start_date = check_date_arg(start)
    end_date = check_date_arg(end)
    # ensure start date < end date
    msg = 'Start date "{}" must be before the end date "{}".'
    assert start_date < end_date, msg.format(str(start_date), str(end_date))

    return start_date, end_date


def check_for_error(func):
    """
    Decorator to check whether the API call returned an error. If an error is returned, raise an exception.
    """
    def api_call(date):
        rsp = func(date)
        if 'error' in rsp:
            raise Exception(rsp['error'])
        return rsp
    return api_call


@check_for_error
def get_api_response(date):
    """
    Call the stock exchange API and return the decoded response.

    Args:
        date(datetime.datetime.date): Date used to query API

    Returns:
        dict: Decoded API response
    """
    rsp = requests.get('https://api.exchangeratesapi.io/{}?base={}'.format(date.strftime('%Y-%m-%d'), args.base))
    return json.loads(rsp.content.decode())


def get_insert_statement_and_values(rsp, date, table_name, rate_keys, base_rate):
    """
    Accumulate the INSERT statement and values. Return the statement and values as a tuple.

    Args:
        response(dict): Single date API response
        date(str): Date to be included in insert statement in format '%Y-%m-%d'

    Returns:
        tuple: INSERT statement (str) and the associated values (tuple)
    """
    statement = 'INSERT INTO {} VALUES (?,?,'.format(table_name) + '?,'*(len(rate_keys)-1) + '?);'
    values = tuple([date, rsp['base']] + [1.0 if x == base_rate else rsp['rates'][x] for x in rate_keys])

    return statement, values


def insert_into_table(statement, values):
    """
    Insert the values into the table.

    Args:
        statement(str): INSERT statement to be committed
        values(tuple): Values to be included in INSERT statement

    Returns:
        None
    """
    try:
        c.execute(statement, values)
    except sqlite3.IntegrityError:
        pass


def validate_date(dt, date_label, valid_dates, table_name):
    """
    Check to make sure given date exists in table.

    Args:
        dt(str): string representation ('YYYY-MM-DD') of start or end date
        date_label(str): label associated with dt ('start'|'end')
        valid_dates(list): list of dates that exist in table
        table_name(str): name of table

    Returns:
        None
    """
    msg = "The {} date '{}' is not in the table '{}'. Include the -p flag to populate the table with the date range."
    assert dt in valid_dates, msg.format(date_label, dt, table_name)


def visualize_exchange_rates(rates, base_rate, dates):
    """
    Visualize exchange rates table for given date range.

    Args:
        rates(dict): countries and their associated exchange rates for given date range
        base_rate(str): base rate country
        dates(list): range of dates to be visualized

    Returns:
        None
    """
    # the number of bins on the x-axis of the plot
    num_bins = 8 if len(dates) >= 8 else len(dates)
    indexes = np.linspace(0, len(dates)-1, num_bins).astype(int)
    # get the xticklabels (i.e. dates)
    xticklabels = [dates[index] for index in indexes]
    # graph the data
    fig, ax = plt.subplots(figsize=(16,6))
    for r in rates:
        plt.plot(rates[r], label=r)
    xmin, xmax = ax.get_xlim()
    ax.set_xticks(np.round(np.linspace(0, xmax+xmin, num_bins), 2))
    ax.set_xticklabels(xticklabels)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Exchange Rate', fontsize=12)
    non_base_currencies = list(rates.keys())
    non_base_currencies.remove(base_rate)
    title = 'Exchange Rates for ' + '{}, '*(len(rates)-1)
    title = title.rstrip(', ').format(*non_base_currencies) + '\nWhen Base Rate is {} Currency'.format(base_rate)
    plt.title(title, fontsize=18)
    plt.legend()
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Acquire query parameters for call to API.')
    parser.add_argument('-b', '--base', default='USD', metavar='',
                        help='Base currency (default: USD).')
    parser.add_argument('-s', '--start', default=datetime(year=2019, month=5, day=1).date(), metavar='',
                        help='Start date of exchange rates history query. Form of date should be YYYY-MM-DD (default: 2019-05-01).')
    parser.add_argument('-e', '--end', default=datetime.now().date(), metavar='',
                        help="End date of exchange rates history query. Form of date should be YYYY-MM-DD (default: Today's date).")
    parser.add_argument('-c', '--countries', default='USD,CAD', metavar='',
                        help='Comma separated list of countries to include in the comparative exchange plot (Default: USD,CAD).')
    parser.add_argument('-p', '--populate', action='store_true',
                        help='Whether to populate the table from the start date up to and including the end date.')
    parser.add_argument('-v', '--visualize', action='store_true',
                        help='Whether to include a visualization of comparative exchange rates.')
    parser.add_argument('-u', '--update', action='store_true',
                        help='Whether to run the daily update code (NOTE: this code will run indefinitely).')
    args = parser.parse_args()

    if not any([args.populate, args.visualize, args.update]):
        msg = 'None of the behavior args (-p, -v, -u) were provided so no action will be taken.'
        warnings.warn(msg, RuntimeWarning)
        sys.exit()

    TABLE_NAME = 'exchange_rates'
    days = list(calendar.day_name)
    # numerical values associated with day names
    # see help(datetime.datetime.isoweekday)
    isoweekdays = dict(zip(range(1, len(days)+1), days))

    # get start and end dates
    start_date, end_date = extract_dates(args.start, args.end)
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days+1)]

    # request data from the API to get the country IDs
    response = get_api_response(start_date)
    rate_keys = list(response['rates'].keys())
    # the full list of table column names
    table_keys = ['date', 'base'] + rate_keys

    # check to make sure the countries (if user provided) are valid
    countries = [x.strip() for x in args.countries.split(',')]
    set_diff = set(countries).difference(set(rate_keys))
    msg = 'The following currencies provided are not valid: {}.\n'
    msg += 'List of valid currencies: {}'
    assert not len(set_diff), msg.format(set_diff, rate_keys)

    # generate the CREATE TABLE statement
    create_table_statement = 'CREATE TABLE IF NOT EXISTS {} ('.format(TABLE_NAME)
    create_table_statement += '\n\tdate TEXT PRIMARY KEY,\n\tbase TEXT,'
    for cnt, value in enumerate(rate_keys):
        comma = '' if cnt == len(rate_keys)-1 else ','
        create_table_statement = create_table_statement + '\n\t{} REAL{}'.format(value, comma)
    create_table_statement += '\n)'

    # create the database and connect to it
    with sqlite3.connect('exchange_rates.db') as conn:
        c = conn.cursor()
        # check to see if table exists for plotting in case the user does not choose to repopulate
        # the table but chooses to plot, in which case, raise an exception
        c.execute('SELECT name FROM sqlite_master WHERE name="{}"'.format(TABLE_NAME))
        table_exists = len(c.fetchall()) # value used in visualize step
        # create the table (if it doesn't exist)
        c.execute(create_table_statement)

        # =========================
        # POPULATE/REPOPULATE TABLE
        # =========================
        if args.populate:
            # truncate table
            c.execute('DELETE FROM {};'.format(TABLE_NAME))
            print("Populating table '{}'...".format(TABLE_NAME))
            # accumulate all of the data from start date up to and including today
            for dt in tqdm(date_range):
                # if not a weekend, then request updated exchange rates
                if isoweekdays[dt.isoweekday()] not in ['Saturday', 'Sunday']:
                    response = get_api_response(dt)
                statement, values = get_insert_statement_and_values(
                    rsp=response, date=str(dt), table_name=TABLE_NAME, rate_keys=rate_keys, base_rate=args.base)
                insert_into_table(statement, values)
            print("Done - table populated from {} to {}.".format(start_date, end_date))

        # ====================
        # CREATE VISUALIZATION
        # ====================
        if args.visualize:
            if not table_exists:
                msg = 'The table "{}" is not populated. Include the -p flag to populate the table before plotting.'.format(TABLE_NAME)
                raise Exception(msg)
            c.execute('SELECT date FROM {};'.format(TABLE_NAME))
            dates_in_table = [x[0] for x in c.fetchall()]
            # check the provided dates are in the table
            validate_date(str(start_date), 'start', dates_in_table, TABLE_NAME)
            validate_date(str(end_date), 'end', dates_in_table, TABLE_NAME)
            if args.base not in countries:
                countries.append(args.base)
            select_statement = 'SELECT ' + '{},'*len(countries)
            select_statement = select_statement.rstrip(',').format(*countries) + '\nFROM {}'.format(TABLE_NAME)
            select_statement += '\nWHERE date IN {};'.format(tuple([str(d) for d in date_range]))
            c.execute(select_statement)
            data = c.fetchall()
            # isolate rates
            rates = {}
            for index, country in enumerate(countries):
                rates[country] = [x[index] for x in data]
            visualize_exchange_rates(rates, args.base, date_range)

        # ==================
        # DAILY TABLE UPDATE
        # ==================
        if args.update:
            _ = input("Press [ENTER] to begin daily table update.")
            print('Daily update has begun.\nNote: This update will run indefinitely unless killed.')
            # loop to run indefinitely to gather daily update
            # determine the next day. When it arrives, we need to call the API
            if table_exists:
                # get the max date and add one day
                c.execute('SELECT MAX(date) FROM {};'.format(TABLE_NAME))
                query_date = datetime.fromisoformat(c.fetchone()[0]).date() + timedelta(days=1)
            else:
                query_date = datetime.now().date()
            while True:
                today_date = datetime.now().date()
                if today_date > query_date:
                    response = get_api_response(query_date)
                    statement, values = get_insert_statement_and_values(
                        rsp=response, date=str(query_date), table_name=TABLE_NAME, rate_keys=rate_keys, base_rate=args.base)
                    print('Updating table for {}...'.format(query_date))
                    insert_into_table(statement, values)
                    print('Done - table updated.'.format(query_date))
                    query_date += timedelta(days=1)
