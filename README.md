# Exchange Rates API
Author: Michael Trossbach

Contact: mptrossbach@gmail.com

Data from: https://exchangeratesapi.io

I decided to query for each date individually because querying a date range was resulting in ambiguous
results for the values of holidays. Querying individual days forces the API to tell you what the correct
values are for that day.

## Comparative Plot of Exchange Rates

![alt text](https://raw.githubusercontent.com/michotross257/ExchangeRatesAPI/master/ExchangeRateComparisonPlot.png)

## Usage
**FLAGS** (one or more must be chosen for any behavior):

> - `-r`: populate the `exchange_rates` table
> - `-p`: generate a comparative plot of exchange rates
> - `-u`: update `exchange_rates` table each day indefinitely
>
> **NOTE**: If you try to plot without populating the table, an exception will be raised.

### Example Scenarios

**Populate (or repopulate) table from start date up to and including end date**
```
$ python ExchangeRatesAPI.py -r
```
**Populate table using new base currency of CAD**
```
$ python ExchangeRatesAPI.py -r -b CAD
```
**Populate table from 2019-01-01 to 2019-02-01**
```
$ python ExchangeRatesAPI.py -r -s 2019-01-01 -e 2019-02-01
```
**Plot CAD, MXN, BGN against base currency of EUR from 2019-01-01 to Today *without* repopulating the table**
```
$ python ExchangeRatesAPI.py -p -b EUR -s 2019-02-01 -c CAD,MXN,BGN
```
> **NOTE**: If you try to plot a date(s) not in the table without the `-r` flag, then an exception will be raised.

**Populate the table using default currency (USD) using the default date range (2019-05-01 to Today), plot USD vs CAD, then allow the update feature to run indefinitely**
```
$ python ExchangeRatesAPI.py -r -p -u
```
