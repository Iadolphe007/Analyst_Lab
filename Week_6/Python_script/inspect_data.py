"""
01_inspect_data.py - Track A, Task 1: prepare and inspect the data.
Independently validates every data-quality observation listed in the assignment.
Outputs: 07_Analysis_Outputs/dq_*.csv and 07_Analysis_Outputs/data_quality_summary.json
"""
import json
import pandas as pd
import sp500_utils as u

raw = pd.read_csv(u.RAW_CSV, encoding="utf-8-sig")          # as supplied (date still text)
df = u.load_raw()                                           # date parsed
u.OUT.mkdir(exist_ok=True)

checks = {}
checks["records"] = len(raw)
checks["columns"] = list(raw.columns)
checks["dtypes_as_supplied"] = {c: str(t) for c, t in raw.dtypes.items()}
checks["unique_symbols"] = int(raw["symbol"].nunique())
checks["distinct_dates"] = int(df["date"].nunique())
checks["date_min"] = str(df["date"].min().date())
checks["date_max"] = str(df["date"].max().date())
checks["missing_values"] = {c: int(v) for c, v in raw.isna().sum().items()}
checks["duplicate_symbol_date"] = int(df.duplicated(["symbol", "date"]).sum())
checks["zero_volume_rows"] = int((df["volume"] == 0).sum())
checks["raw_file_sorted_by_symbol_date"] = bool(
    df.equals(df.sort_values(["symbol", "date"]).reset_index(drop=True)))
checks["raw_file_sorted_by_date_then_symbol"] = bool(
    df.equals(df.sort_values(["date", "symbol"]).reset_index(drop=True)))

p = u.prepare(df)
checks["ohlc_inconsistent_rows"] = int(p["ohlc_inconsistent"].sum())
checks["moves_over_25pct_total"] = int((p["daily_return_pct"].abs() > u.LARGE_MOVE_PCT).sum())
checks["non_market_events_excluded"] = int(p["extreme_move"].sum())
checks["large_moves_retained_flagged"] = int(p["large_move"].sum())
checks["non_positive_close"] = int((df["close"] <= 0).sum())

# ---- detail tables -------------------------------------------------------
cols = ["symbol", "date", "open", "high", "low", "close", "volume"]
df[df[["open", "high", "low"]].isna().any(axis=1)][cols].to_csv(u.OUT / "dq_missing_ohl_rows.csv", index=False)
df[df["volume"] == 0][cols].to_csv(u.OUT / "dq_zero_volume_rows.csv", index=False)
p[p["ohlc_inconsistent"]][cols].to_csv(u.OUT / "dq_ohlc_inconsistent_rows.csv", index=False)

ext = p[p["extreme_move"] | p["large_move"]][["symbol", "date", "close", "daily_return_pct", "volume", "extreme_move"]].copy()
ext["prev_close"] = ext["close"] / (1 + ext["daily_return_pct"] / 100)
ext["treatment"] = ext["extreme_move"].map({True: "EXCLUDED from return/volatility stats (probable non-market event)", False: "RETAINED (large move, treated as genuine market move)"})
ext["note"] = [u.NON_MARKET_EVENTS.get((s, d.strftime("%Y-%m-%d")), "") for s, d in zip(ext["symbol"], ext["date"])]
ext = ext.drop(columns="extreme_move").sort_values("daily_return_pct")
ext.to_csv(u.OUT / "dq_large_moves.csv", index=False)

cov = (df.groupby("symbol")["date"].agg(first_date="min", last_date="max", trading_days="count")
         .assign(missing_days=lambda x: df["date"].nunique() - x["trading_days"]))
cov = cov[cov["missing_days"] > 0].sort_values("trading_days")
cov.to_csv(u.OUT / "dq_incomplete_histories.csv")
checks["symbols_with_incomplete_history"] = int(len(cov))
checks["symbols_late_start_or_early_end"] = int(
    ((cov["first_date"] > df["date"].min() + pd.Timedelta(days=10)) | (cov["last_date"] < df["date"].max())).sum())

# a few extremes for context
checks["max_close"] = df.loc[df["close"].idxmax(), ["symbol", "date", "close"]].astype(str).to_dict()
checks["min_close"] = df.loc[df["close"].idxmin(), ["symbol", "date", "close"]].astype(str).to_dict()
checks["max_volume"] = df.loc[df["volume"].idxmax(), ["symbol", "date", "volume"]].astype(str).to_dict()

# do the zero-volume placeholder rows simply repeat the previous close?
zv = p[p["zero_volume"]][["symbol", "date", "close", "daily_change", "daily_return_pct"]]
zv.to_csv(u.OUT / "dq_zero_volume_vs_prev_close.csv", index=False)

with open(u.OUT / "data_quality_summary.json", "w") as f:
    json.dump(checks, f, indent=2, default=str)
print(json.dumps(checks, indent=2, default=str))
print("\nZero-volume rows vs previous close:\n", zv.to_string(index=False))
print("\nLarge moves (>25%):\n", ext.to_string(index=False))
