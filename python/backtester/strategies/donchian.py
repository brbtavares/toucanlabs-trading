from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


TriggerMode = Literal["cross", "close_beyond"]


@dataclass
class DonchianParams:
	donch_len: int = 20
	atr_len: int = 14
	min_atr_pct: float = 0.0
	trigger: TriggerMode = "cross"


class DonchianStrategy:
	def __init__(self, params: DonchianParams):
		self.p = params

	def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
		d = df.copy()

		# Donchian bands with 1-bar shift to reduce repaint
		d["donch_high_raw"] = d["high"].rolling(self.p.donch_len, min_periods=1).max()
		d["donch_low_raw"] = d["low"].rolling(self.p.donch_len, min_periods=1).min()
		d["upper"] = d["donch_high_raw"].shift(1)
		d["lower"] = d["donch_low_raw"].shift(1)
		d["basis"] = (d["upper"] + d["lower"]) / 2.0

		# ATR (classic Wilder) approximation using True Range rolling mean
		tr1 = (d["high"] - d["low"]).abs()
		tr2 = (d["high"] - d["close"].shift(1)).abs()
		tr3 = (d["low"] - d["close"].shift(1)).abs()
		tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
		d["atr"] = tr.rolling(self.p.atr_len, min_periods=1).mean()

		# Volatility filter in percent
		d["atr_pct"] = (d["atr"] / d["close"]) * 100.0
		d["vol_ok"] = d["atr_pct"] >= float(self.p.min_atr_pct)

		# Cross events
		up = d["upper"]
		lo = d["lower"]
		c = d["close"]
		d["cross_up_upper"] = (c > up) & (c.shift(1) <= up.shift(1))
		d["cross_down_lower"] = (c < lo) & (c.shift(1) >= lo.shift(1))
		d["cross_down_upper"] = (c < up) & (c.shift(1) >= up.shift(1))
		d["cross_up_lower"] = (c > lo) & (c.shift(1) <= lo.shift(1))

		# Trigger modes
		if self.p.trigger == "cross":
			entry_long_trig = d["cross_up_upper"]
			entry_short_trig = d["cross_down_lower"]
		else:  # close_beyond
			entry_long_trig = c > up
			entry_short_trig = c < lo

		d["entry_long"] = d["vol_ok"] & entry_long_trig
		d["entry_short"] = d["vol_ok"] & entry_short_trig
		d["exit_long"] = d["cross_down_upper"] | d["entry_short"]
		d["exit_short"] = d["cross_up_lower"] | d["entry_long"]

		# Risk heuristics (optional): distance to lower/upper band
		d["risk_long"] = (d["close"] - d["lower"]).abs()
		d["risk_short"] = (d["upper"] - d["close"]).abs()

		return d

