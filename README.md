# Exchange Rate API
Author: Michael Trossbach

Contact: mptrossbach@gmail.com

Data from: https://exchangeratesapi.io

I decided to query for each date individually because querying a date range was resulting in ambiguous
results for the values of holidays. Querying individual days forces the API to tell you what the correct
values are for that day.

## Comparative Plot of Exchange Rates

![alt text](https://raw.githubusercontent.com/michotross257/ExchangeRateAPI/master/ExchangeRateComparisonPlot.png)

## Usage
**FLAGS** (one or more must be chosen for any behavior):

	1. Populate the table: -r
	2. Comparative plot: -p
	3. Update table each day indefinitely: -u

> NOTE: If you try to plot without populating the table, an exception will be raised.

### Example Scenarios

#### Populate (or repopulate) table from start date up to and including end date
`$ python ExchangeRateAPI.py -r`
#### Populate table using new base currency of CAD
`$ python ExchangeRateAPI.py -r -b CAD`
#### Populate table from 2019-01-01 to 2019-02-01
`$ python ExchangeRateAPI.py -r -s 2019-01-01 -e 2019-02-01`
#### Plot CAD, MXN, BGN against base currency of EUR from 2019-01-01 to Today WITHOUT repopulating the table
`$ python ExchangeRateAPI.py -p -b EUR -s 2019-02-01 -c CAD,MXN,BGN`
> NOTE: If you try to plot a date(s) not in the table without the -r flag, then an exception will be raised.
#### Populate the table using default currency (USD) using the default date range (2019-05-01 to Today), plot USD vs CAD, then allow the update feature to run indefinitely
`$ python ExchangeRateAPI.py -r -p -u`
