# Exchange Rates API
Author: Michael Trossbach

Contact: mptrossbach@gmail.com

## Overview

Data from: https://exchangeratesapi.io

I decided to query for each date individually because querying a date range was resulting in ambiguous
results for the values of holidays. Querying individual days forces the API to tell you what the correct
values are for that day.

## Comparative Plot of Exchange Rates

![alt text](https://raw.githubusercontent.com/michotross257/exchange-rates-api/master/images/ExchangeRateComparisonPlot.png)

## Usage
**FLAGS** (one or more must be chosen for any behavior):

> - `-p`: populate the `exchange_rates` table
> - `-v`: generate a comparative visualization of exchange rates
> - `-u`: update `exchange_rates` table each day indefinitely
>
> **NOTE**: If you try to plot without populating the table, an exception will be raised.

### Example Scenarios

**Populate table using default date range (2019-05-01 to today) and base currency (USD)**
```
$ python ExchangeRatesAPI.py -p
```
**Populate table using default date range and new base currency of CAD**
```
$ python ExchangeRatesAPI.py -p -b CAD
```
**Populate table from 2019-01-01 to 2019-02-01**
```
$ python ExchangeRatesAPI.py -p -s 2019-01-01 -e 2019-02-01
```
**Visualize CAD, MXN, BGN against base currency of EUR from 2019-02-01 to Today *without* repopulating the table**
```
$ python ExchangeRatesAPI.py -v -b EUR -s 2019-02-01 -c CAD,MXN,BGN
```
> **NOTE**: If you try to visualize a date that is not in the table without including the `-p` flag, then an exception will be raised.

**Populate the table using default currency (USD) using the default date range (2019-05-01 to today), plot USD vs CAD, then allow the update feature to run indefinitely**
```
$ python ExchangeRatesAPI.py -p -v -u
```
