import argparse
import pathlib
from dataclasses import dataclass
from typing import List, Optional, Dict

import numpy as np
import pandas as pd

# Local strategies
from .strategies.donchian import DonchianStrategy, DonchianParams


@dataclass
class Trade:
	side: str  # "long" or "short"
	entry_time: pd.Timestamp
	exit_time: pd.Timestamp
	entry_price: float
	exit_price: float
	size: float
	risk_price: float  # distance in price units used for R calc

	@property
	def pnl_abs(self) -> float:
		sign = 1.0 if self.side == "long" else -1.0
		return (self.exit_price - self.entry_price) * sign * self.size

	@property
	def pnl_r(self) -> float:
		if self.risk_price <= 0:
			return np.nan
		return self.pnl_abs / (self.risk_price * self.size)


def load_price_csv(path: pathlib.Path) -> pd.DataFrame:
	df = pd.read_csv(path)
	# Expected columns: timestamp, open, high, low, close, volume
	cols = {c.lower(): c for c in df.columns}
	required = ["timestamp", "open", "high", "low", "close", "volume"]
	missing = [c for c in required if c not in [k.lower() for k in df.columns]]
	if missing:
		raise ValueError(f"CSV missing required columns: {missing}")

	# Normalize columns
	df = df.rename(columns={cols.get("timestamp"): "timestamp",
							cols.get("open"): "open",
							cols.get("high"): "high",
							cols.get("low"): "low",
							cols.get("close"): "close",
							cols.get("volume"): "volume"})
	df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
	df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
	return df


def run_backtest(df: pd.DataFrame,
				 strategy_name: str,
				 strategy_params: Dict,
				 symbol: Optional[str] = None) -> pd.DataFrame:
	# Prepare strategy
	if strategy_name.lower() == "donchian":
		params = DonchianParams(**strategy_params)
		strat = DonchianStrategy(params)
	else:
		raise ValueError(f"Unknown strategy: {strategy_name}")

	df_sig = strat.prepare(df.copy())

	trades: List[Trade] = []
	state = "flat"
	entry_idx: Optional[int] = None
	entry_price = 0.0
	risk_price = 0.0
	size = float(strategy_params.get("size", 1.0))

	# Iterate bars; execute at next open to avoid lookahead bias
	for i in range(1, len(df_sig) - 1):
		row = df_sig.iloc[i]

		# Exits first (based on current bar, filled next bar)
		if state == "long":
			if row["exit_long"]:
				exit_price = float(df_sig.iloc[i + 1]["open"])  # next bar open
				trades.append(Trade(
					side="long",
					entry_time=df_sig.iloc[entry_idx]["timestamp"],
					exit_time=df_sig.iloc[i + 1]["timestamp"],
					entry_price=float(entry_price),
					exit_price=exit_price,
					size=size,
					risk_price=float(risk_price)
				))
				state = "flat"; entry_idx = None
				continue
		elif state == "short":
			if row["exit_short"]:
				exit_price = float(df_sig.iloc[i + 1]["open"])  # next bar open
				trades.append(Trade(
					side="short",
					entry_time=df_sig.iloc[entry_idx]["timestamp"],
					exit_time=df_sig.iloc[i + 1]["timestamp"],
					entry_price=float(entry_price),
					exit_price=exit_price,
					size=size,
					risk_price=float(risk_price)
				))
				state = "flat"; entry_idx = None
				continue

		# Entries when flat (filled next bar)
		if state == "flat":
			if row["entry_long"]:
				# Risk distance: distance to lower band or ATR-based fallback
				risk = float(max(row.get("risk_long", np.nan), 0))
				if not np.isfinite(risk) or risk <= 0:
					risk = float(max(row.get("atr", np.nan), 0))
				state = "long"
				entry_idx = i + 1
				entry_price = float(df_sig.iloc[i + 1]["open"])  # next bar open
				risk_price = risk
			elif row["entry_short"]:
				risk = float(max(row.get("risk_short", np.nan), 0))
				if not np.isfinite(risk) or risk <= 0:
					risk = float(max(row.get("atr", np.nan), 0))
				state = "short"
				entry_idx = i + 1
				entry_price = float(df_sig.iloc[i + 1]["open"])  # next bar open
				risk_price = risk

	# Convert to DataFrame compatible with report.py
	out_rows = []
	for t in trades:
		out_rows.append({
			"side": t.side,
			"entry_time": t.entry_time,
			"exit_time": t.exit_time,
			"entry_price": t.entry_price,
			"exit_price": t.exit_price,
			"size": t.size,
			"risk_price": t.risk_price,
			"pnl_abs": t.pnl_abs,
			"pnl_r": t.pnl_r,
			**({"symbol": symbol} if symbol else {})
		})
	return pd.DataFrame(out_rows)


def main():
	parser = argparse.ArgumentParser(description="CSV-based backtester")
	parser.add_argument("--data", type=str, help="Path to CSV file or directory containing CSVs.")
	parser.add_argument("--output", type=str, default="output", help="Output directory for trades CSVs.")
	parser.add_argument("--strategy", type=str, default="donchian", choices=["donchian"], help="Strategy to run.")
	# Donchian params
	parser.add_argument("--donch-len", type=int, default=20)
	parser.add_argument("--atr-len", type=int, default=14)
	parser.add_argument("--min-atr-pct", type=float, default=0.0)
	parser.add_argument("--trigger", type=str, default="cross", choices=["cross","close_beyond"], help="Entry trigger mode.")
	parser.add_argument("--size", type=float, default=1.0, help="Position size (units).")

	args = parser.parse_args()

	data_path = pathlib.Path(args.data)
	out_dir = pathlib.Path(args.output)
	out_dir.mkdir(parents=True, exist_ok=True)

	files: List[pathlib.Path]
	if data_path.is_dir():
		files = sorted([p for p in data_path.glob("*.csv")])
	else:
		files = [data_path]

	for f in files:
		df = load_price_csv(f)
		symbol = f.stem
		trades = run_backtest(
			df,
			strategy_name=args.strategy,
			strategy_params={
				"donch_len": args.donch_len,
				"atr_len": args.atr_len,
				"min_atr_pct": args.min_atr_pct,
				"trigger": args.trigger,
				"size": args.size,
			},
			symbol=symbol,
		)

		out_file = out_dir / f"trades_{args.strategy}_{symbol}.csv"
		trades.to_csv(out_file, index=False)
		print(f"Wrote {len(trades)} trades -> {out_file}")


if __name__ == "__main__":
	main()

