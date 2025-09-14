import pandas as pd, numpy as np, matplotlib.pyplot as plt, json, pathlib, datetime as dt

def load_trades(csv_path):
    df = pd.read_csv(csv_path, parse_dates=["entry_time","exit_time"])
    df = df.sort_values("exit_time").reset_index(drop=True)
    # equity em R: soma cumulativa de pnl_r por trade
    df["equity_R"] = df["pnl_r"].cumsum()
    return df

def max_drawdown(series):
    peak = series.cummax()
    dd = series - peak
    dd_pct = dd / (peak.replace(0, np.nan))
    return dd.min(), dd_pct.min()

def sharpe_from_daily(equity_series, tz="America/Sao_Paulo", trading_days=252):
    # converte equity por trade para equity diário (último valor do dia)
    s = equity_series.copy()
    # supondo equity_R; transforme em retorno diário em R
    eq = s.rename("equity").to_frame()
    eq["date"] = eq.index.floor("D")
    daily = eq.groupby("date")["equity"].last().ffill().dropna()
    ret = daily.diff().dropna()  # R por dia
    if ret.std() == 0 or np.isnan(ret.std()):
        return np.nan
    return (ret.mean() / ret.std()) * np.sqrt(trading_days)

def make_plots(df, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    # Equity curve (em R)
    plt.figure()
    plt.plot(df["exit_time"], df["equity_R"])
    plt.title("Equity Curve (R)")
    plt.xlabel("Time"); plt.ylabel("Equity (R)")
    plt.tight_layout(); plt.savefig(outdir/"equity_curve.png"); plt.close()

    # Drawdown (em R)
    eq = df.set_index("exit_time")["equity_R"]
    dd, _ = max_drawdown(eq)
    peak = eq.cummax()
    drawdown = eq - peak
    plt.figure()
    plt.plot(drawdown.index, drawdown.values)
    plt.title("Drawdown (R)")
    plt.xlabel("Time"); plt.ylabel("Drawdown (R)")
    plt.tight_layout(); plt.savefig(outdir/"drawdown.png"); plt.close()

    # Histogram PnL (R)
    plt.figure()
    plt.hist(df["pnl_r"].values, bins=40)
    plt.title("PnL per Trade (R)")
    plt.xlabel("R"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(outdir/"pnl_hist.png"); plt.close()

def summarize(df):
    eq = df["equity_R"]
    pf = df.loc[df["pnl_r"]>0, "pnl_r"].sum() / max(1e-12, -df.loc[df["pnl_r"]<0, "pnl_r"].sum())
    md, _ = max_drawdown(eq)
    sharpe = sharpe_from_daily(eq.set_axis(df["exit_time"].values))
    return {
        "trades": int(len(df)),
        "win_rate": float((df["pnl_r"]>0).mean()),
        "profit_factor": float(pf),
        "expectancy_R": float(df["pnl_r"].mean()),
        "max_drawdown_R": float(md),
        "sharpe": None if pd.isna(sharpe) else float(sharpe)
    }

def run(csv_path, outdir, meta):
    df = load_trades(csv_path)
    make_plots(df, outdir)
    metrics = summarize(df)
    metrics.update(meta)
    with open(pathlib.Path(outdir)/"metrics.json","w") as f:
        json.dump(metrics, f, indent=2)

# Exemplo:
# run("reports/MAxATR_WINM25_H1_2025-09-14/trades.csv",
#     "reports/MAxATR_WINM25_H1_2025-09-14/",
#     {"symbol":"WINM25","timeframe":"H1","period":{"start":"2024-01-02","end":"2025-06-28"}})
