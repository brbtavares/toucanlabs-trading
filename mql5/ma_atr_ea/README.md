MA + ATR Expert Advisor (MetaTrader 5)

## Folder structure

```
mql5/
  ma_atr_ea/
    ma_atr_ea.mq5          # Expert Advisor source (MT5 / MQL5)
    media/
      USDJPYH1.png         # Example chart (optional)
      TesterGraphReport2025.09.14.png  # Example tester graph
    README.md              # This file
```

## What it does

This MT5 Expert Advisor trades a simple Moving Average crossover strategy with flexible stop-loss and take-profit modes. It supports:

- Fast/Slow MA crossover entries (on bar close; no intrabar repaint) 
- Optional ATR% filter to avoid low-volatility entries
- Multiple SL/TP modes: Money (account currency), Percent, Points, or ATR multipliers
- One position per symbol; optional close-and-reverse on opposite signal

It is intended for educational purposes and quick prototyping/backtesting.

## Strategy overview

- Entry Long: Fast MA crosses above Slow MA (evaluated at the close of the previous bar)
- Entry Short: Fast MA crosses below Slow MA
- Optional: If an opposite position is open and “Allow Reverse” is enabled, the EA closes it and opens a new one in the opposite direction
- SL/TP are computed at order placement per your selected mode and are sent with the trade

## Inputs

Trading and Routing:
- Lots (InpLots): Position size in lots
- Allow Longs / Allow Shorts (InpAllowLongs / InpAllowShorts)
- Allow Reverse (InpAllowReverse): Close opposite and flip when a new signal appears
- Magic Number (InpMagic): Identifier for the EA’s positions

MA / ATR:
- MA Method (InpMAMethod): e.g., EMA, SMA
- Applied Price (InpPrice): PRICE_CLOSE, etc.
- Fast MA Length (InpFastLen)
- Slow MA Length (InpSlowLen)
- ATR Length (InpATRLen)
- Min ATR% to allow entry (InpMinATRPct): 0 disables the ATR filter

Stop/Target Modes (InpSLMode / InpTPMode):
- NONE: No stop or target
- MONEY: Fixed amount in account currency per position
- PERCENT: Percent of entry price (e.g., 0.5 = 0.5%)
- POINTS: Fixed points (price points)
- ATR: K × ATR, using InpSL_ATR_K / InpTP_ATR_K

Mode-specific parameters:
- MONEY: InpSL_Money, InpTP_Money
- PERCENT: InpSL_Pct, InpTP_Pct
- POINTS: InpSL_Points, InpTP_Points
- ATR: InpSL_ATR_K, InpTP_ATR_K

Execution/Misc:
- Process only once per bar (InpProcessOnClose): Recommended true
- Verbose (InpVerbose): Log diagnostics to the Experts tab

## How SL/TP are built

At entry time, the EA converts your chosen mode to a price distance and sets absolute SL/TP levels:
- MONEY → MoneyToPriceDist via tickvalue and ticksize
- PERCENT → entry_price × (percent/100)
- POINTS → points × point value
- ATR → K × ATR

It also enforces broker minimum stop distance (SYMBOL_TRADE_STOPS_LEVEL).

## How to use (MT5)

1) Open MetaTrader 5 and MetaEditor
2) Place `ma_atr_ea.mq5` under MQL5/Experts (or import into your project)
3) Compile in MetaEditor (F7); fix any platform-specific warnings if needed
4) In MT5, attach the EA to a chart of your choice
5) Enable Algo Trading and configure inputs (lots, MA lengths, SL/TP mode, ATR filter, etc.)
6) For live/demo trading, ensure your broker allows automated trading and symbol settings are correct

## Calibration guidelines

- Start with Fast=9 / Slow=21 on H1/H4; adapt per symbol
- ATR filter: For quiet markets, try 0.05–0.20 (%). For volatile assets, 0.20–0.80 (%)
- SL/TP mode:
  - ATR mode is adaptive and robust across symbols
  - Percent mode aligns with relative moves
  - Money mode ensures fixed risk in account currency (be mindful of symbol tickvalue)
  - Points mode is simple but symbol-specific
- If overtrading: Increase Slow MA or ATR% threshold
- If undertrading: Decrease thresholds or shorten MA lengths

## Limitations

- One position per symbol at a time; no partial close/scale-in/out logic by default
- No trailing stops or break-even shifts (can be added)
- SL/TP are set once at entry; the EA does not manage/modify orders after
- Signals are based on bar close; intrabar crosses are ignored by design
- Broker execution, spreads, swaps, and slippage are not modeled beyond MT5 tester behavior

## Backtesting tips

- Use “Open prices only” or “1-minute OHLC” for quick passes; switch to “Every tick” for accuracy
- Ensure your symbol has sufficient history and correct contract specifications
- Validate that SL/TP distances exceed the broker’s stops level to avoid rejected orders
- Try several SL/TP modes and ATR thresholds to understand sensitivity

## Media

- See images in `media/` for example charts and tester results:
  - `media/USDJPYH1.png`
  - `media/TesterGraphReport2025.09.14.png`

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Disclaimer

Educational purposes only. Not financial advice. Trading involves risk.
