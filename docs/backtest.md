# Backtest

## Description

* Display all available strategies
* Choose which strategy to backtest
* display strategy code content and any other meta-data
* trigger strategy to run
* display backtest results (datetime and PnL)
* save backtest results

## Strategy Requirement

* must be a single python file
* must conform to project version and must use the same package and version as the project.
* every strategy must specify data sources on the `backtest.cfg` file.

## How to read `.cfg` file

```python
import configparser
config = configparser.ConfigParser()
config.read("cfg file path")
locations = config.get('s3_locations', '-').get('locations', '-')
```