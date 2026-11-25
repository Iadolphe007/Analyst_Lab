"""
02_prepare_data.py - Track A, Task 2: cleaning and preparation.

Cleaning decisions (documented in 09_Documentation/Data_Quality_Assessment):
  * date text (M/D/YYYY) -> datetime; rows sorted by symbol, date.
  * Missing open/high/low are NOT replaced with zero and NOT imputed: they stay
    blank. Daily range is only computed where high AND low exist and are logical.
  * Zero-volume rows are kept (close is valid) but excluded from volume statistics.
  * 9 rows whose OHLC values are logically inconsistent are flagged; the close
    is kept, but the daily range is blanked for them.
  * 13 probable non-market events (spin-offs/splits/special dividend/data glitch)
    are flagged; their daily return is excluded from return & volatility stats.
  * All calculations are per symbol, in date order (no cross-symbol leakage).
Outputs:
  01_Data/processed/*.csv   and   04_PowerBI/data/{Prices,Symbols,Calendar}.csv
"""
import pandas as pd
import sp500_utils as u

u.PROCESSED.mkdir(parents=True, exist_ok=True)
u.PBI_DATA.mkdir(parents=True, exist_ok=True)

raw = u.load_raw()
df = u.prepare(raw)
summ = u.symbol_summary(df)

# ---- processed (analysis) datasets ---------------------------------------
df.to_csv(u.PROCESSED / "sp500_clean_full.csv", index=False, float_format="%.10g", date_format="%Y-%m-%d")
df[df["symbol"].isin(u.SELECTED)].to_csv(
    u.PROCESSED / "sp500_selected_stocks.csv", index=False, float_format="%.10g", date_format="%Y-%m-%d")
summ.to_csv(u.PROCESSED / "symbol_summary.csv", index=False, float_format="%.4f")

# ---- Power BI tables -------------------------------------------------------
prices_cols = ["symbol", "date", "open", "high", "low", "close", "volume",
               "daily_change", "daily_return_pct", "daily_return_clean_pct", "abs_return_pct",
               "return_bin", "daily_range", "daily_range_pct", "ma_5", "ma_20", "ma_50",
               "rolling_vol_20", "cum_return_pct"]
pb = df[prices_cols].copy()
pb["extreme_move_flag"] = df["extreme_move"].astype(int)
pb["large_move_flag"] = df["large_move"].astype(int)
pb["zero_volume_flag"] = df["zero_volume"].astype(int)
pb.to_csv(u.PBI_DATA / "Prices.csv", index=False, float_format="%.4f", date_format="%Y-%m-%d")

sy = summ.copy()
sy["coverage_bucket"] = pd.cut(sy["coverage_pct"], [0, 25, 50, 75, 99.99, 100.01],
                               labels=["<25%", "25-50%", "50-75%", "75-99%", "100%"]).astype(str)
sy["first_year"] = pd.to_datetime(sy["first_date"]).dt.year
sy.to_csv(u.PBI_DATA / "Symbols.csv", index=False, float_format="%.4f")

dates = pd.Series(sorted(df["date"].unique()), name="Date")
cal = pd.DataFrame({"Date": dates})
cal["Year"] = cal["Date"].dt.year
cal["QuarterNum"] = cal["Date"].dt.quarter
cal["Quarter"] = "Q" + cal["QuarterNum"].astype(str)
cal["YearQuarter"] = cal["Year"].astype(str) + "-Q" + cal["QuarterNum"].astype(str)
cal["MonthNum"] = cal["Date"].dt.month
cal["MonthName"] = cal["Date"].dt.strftime("%b")
cal["YearMonth"] = cal["Date"].dt.strftime("%Y-%m")
cal.to_csv(u.PBI_DATA / "Calendar.csv", index=False, date_format="%Y-%m-%d")

print("clean rows:", len(df), "| columns:", df.shape[1])
print("Prices.csv size MB:", round((u.PBI_DATA / "Prices.csv").stat().st_size / 1e6, 1))
print(summ["history_status"].value_counts())
print(df[u.SELECTED[:0] or ["symbol"]].nunique())
chk = summ[summ.symbol.isin(u.SELECTED)][["symbol", "trading_days", "extreme_move_days", "raw_period_return_pct",
                                          "adj_period_return_pct", "annualised_volatility_pct"]]
print(chk.to_string(index=False))
