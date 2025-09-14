# Donchian Breakout + Volatility Filter [ToucanLabs]

## Folder structure

```
pine/
	donchian_breakout/
		donchian_breakout.pine   # TradingView Pine v6 indicator
		README.md                # This guide
		media/                   # Chart (demo)
```

## What this indicator/alert does

This indicator plots a Donchian channel (upper/lower/mid) and signals breakout entries when price exceeds the channel boundary. A volatility filter based on ATR% can be enabled to avoid signals in low-volatility environments. The script is non-repainting by using one-bar-shifted Donchian bands and only generating signals on bar close.

You can set alerts for entries and exits. Entries can be triggered either strictly on cross events (Cross) or when the candle closes beyond the band (CloseBeyond), which can be more permissive when bands “jump”.

## Inputs

- Donchian Length (int): Lookback window for the channel high/low.
- ATR Length (int): ATR period used for the volatility filter.
- Min ATR% (vol filter) (float): Minimum ATR as a percent of price required for signals. Example: 0.2 means ATR must be at least 0.2% of price.
- Use Volatility Filter (bool): Turn the ATR-based filter on/off.
- Entry Trigger (enum):
	- Cross: only emit an entry when price crosses the band on this bar.
	- CloseBeyond: emit an entry when the bar closes beyond the band, even without a strict cross.
- Show Signal Labels (bool): Show labels on the chart for entries and exits.
- Show Debug Markers (bool): Draw small markers indicating raw cross events and when filters block entries.

Note: Some of the options above are available in the enhanced script variant. If you use the minimal variant, only a subset may be present.

## Signals

- Long Entry: price breaks above the upper Donchian band (according to the selected Entry Trigger) and passes the volatility filter (if enabled), while flat (no open state tracked).
- Short Entry: price breaks below the lower band under the same conditions.
- Exit Long: either price crosses back below the upper band or a short entry trigger occurs.
- Exit Short: either price crosses back above the lower band or a long entry trigger occurs.

The script tracks position state (inLong/inShort) to avoid repeated entries and orphan exits.

## Alerts

Create alerts from the indicator using these alertcondition keys:

- TL_LONG_ENTRY: Long: {{ticker}} @ {{close}}
- TL_SHORT_ENTRY: Short: {{ticker}} @ {{close}}
- TL_EXIT_LONG: Exit Long: {{ticker}} @ {{close}}
- TL_EXIT_SHORT: Exit Short: {{ticker}} @ {{close}}

Add the indicator to your chart, open the Alerts panel in TradingView, choose this indicator, and select the desired alertcondition.

## How to use

1) Add the indicator to your TradingView chart (Pine v6).
2) Choose a timeframe and instrument. The indicator runs on your chart’s timeframe.
3) Configure inputs:
	 - Donchian Length: typical values are 20–55; shorter = more signals.
	 - ATR settings: lower Min ATR% yields more signals; increase to filter chop.
	 - Entry Trigger: start with Cross; if entries seem “missed” due to band jumps, try CloseBeyond.
	 - Toggle labels and debug markers as needed.
4) Optionally create alerts for entries/exits (see Alerts section).

## Calibration rules (quick guide)

- Start with Donchian Length = 20 on liquid instruments; increase to 55+ to reduce noise.
- ATR Length 10–14 is common. Adjust Min ATR% by instrument:
	- Forex/indices (tight ranges): 0.05–0.20
	- Large-cap equities: 0.10–0.30
	- Crypto/volatile assets: 0.20–0.80
- If many false signals: raise Min ATR%, increase Donchian Length, or require Cross instead of CloseBeyond.
- If few/missed signals: lower Min ATR%, decrease Donchian Length, or switch to CloseBeyond.
- Use the debug markers to see whether the ATR filter or session constraints are blocking entries.

## Limitations

- Signals are generated on bar close; intrabar moves are not considered.
- In fast markets, gaps can “jump” over bands; CloseBeyond helps but does not guarantee fills.
- The indicator does not manage orders or slippage; use the strategy() version for backtesting and risk controls.
- Alerts depend on TradingView’s alert engine and your plan’s limitations.

## License

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Disclaimer

Educational purposes only. Not financial advice. Trading involves risk.
