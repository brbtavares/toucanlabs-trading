Python Backtester (CSV)

## Data format

Place CSV files under `data/` (or pass a custom path). Each CSV must have columns:

```
timestamp,open,high,low,close,volume
```

Timestamp will be parsed to UTC. Any additional columns are ignored.

## Usage

Run from the repository root or from `python/backtester/` package context. Examples:

```
# Single file
python -m python.backtester.backtest --data data/BTCUSDT_1h.csv --output output --strategy donchian --donch-len 20 --atr-len 14 --min-atr-pct 0.2 --trigger cross --size 1

# All CSVs in a folder
python -m python.backtester.backtest --data data/ --output output --strategy donchian --donch-len 55 --atr-len 14 --min-atr-pct 0.1 --trigger close_beyond --size 1
```

Outputs: a trades CSV per input file, written to `output/`, with columns:

```
side,entry_time,exit_time,entry_price,exit_price,size,risk_price,pnl_abs,pnl_r,symbol
```

You can feed the trades CSV into `report.py` to create plots and metrics.

## Strategies

Currently available: Donchian breakout with ATR filter (`strategies/donchian.py`). Add new strategies by implementing a class with a `prepare(df)` method that returns a DataFrame containing:

```
entry_long, entry_short, exit_long, exit_short [, atr, risk_long, risk_short]
```

## Notes

- Execution is next-bar open to avoid lookahead bias.
- Signals use one-bar shifted Donchian bands to reduce repaint.
- `pnl_r` uses a simple price-distance risk heuristic by default (distance to band or ATR fallback). Adjust per strategy as needed.

