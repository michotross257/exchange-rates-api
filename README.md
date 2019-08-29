# Exchange Rate API
Author: Michael Trossbach

Contact: mptrossbach@gmail.com

Data from: https://exchangeratesapi.io
## Usage
**FLAGS** (one or more must be chosen for any behavior):

	1. Repopulate the table: -r 
	2. Comparative plot: -p
	3. Update table each day indefinitely: -u

> NOTE: If you try to plot without populating the table, an exception will be raised.

### Example Scenarios

#### Populate (& repopulate) table from start date up to and including end date
`$ python ExchangeRateAPI.py -r`
#### Populate table using new base currency of CAD
`$ python ExchangeRateAPI.py -r -b CAD`
#### Populate table from 2019-01-01 to 2019-02-01
`$ python ExchangeRateAPI.py -r -s 2019-01-01 -e 2019-02-01`
#### Plot CAD, MXN, BGN against base currency of EUR from 2019-01-01 to Today
`$ python ExchangeRateAPI.py -r -p -b EUR -s 2019-02-01 -c CAD,MXN,BGN`
> NOTE: If you try to plot a date(s) not in the table without the -r flag, then an exception will be raised.
#### Populate the table where USD is the base currency using the default date range, plot USD vs CAD, then allow the update feature to run indefinitely
`$ python ExchangeRateAPI.py -r -p -u`
