"""
03_analysis.py - Track A, Tasks 3 & 4: market performance + comparative analysis.

Calculation methods (also in 09_Documentation/KPI_Definition_Sheet.xlsx):
  Period return (%)      = (last close / first close - 1) * 100            [raw price return]
  Event-adjusted return  = compounded daily returns, with the 13 flagged non-market
                           days set to 0%                                  [used for ranking]
  Daily volatility (%)   = sample std-dev of clean daily % returns
  Annualised vol (%)     = daily volatility * sqrt(252)
  Rankings of return/volatility use symbols with a FULL-PERIOD history only
  (start within the first 10 days of Jan-2014 and still trading on 2017-12-29).
Outputs -> 07_Analysis_Outputs/*.csv
"""
import numpy as np
import pandas as pd
from scipy import stats
import sp500_utils as u

u.OUT.mkdir(exist_ok=True)
df = pd.read_csv(u.PROCESSED / "sp500_clean_full.csv", parse_dates=["date"])
summ = pd.read_csv(u.PROCESSED / "symbol_summary.csv", parse_dates=["first_date", "last_date",
                                                                      "max_close_date", "min_close_date"])
full = summ[summ["history_status"] == "Full period"].copy()
sel = u.SELECTED
R = {}   # printed headline results

# ---- Q1  highest / lowest closing prices -----------------------------------
q1_hi = summ.nlargest(15, "max_close")[["symbol", "max_close", "max_close_date"]]
q1_lo = summ.nsmallest(15, "min_close")[["symbol", "min_close", "min_close_date"]]
q1_hi.to_csv(u.OUT / "q1_highest_closing_prices.csv", index=False)
q1_lo.to_csv(u.OUT / "q1_lowest_closing_prices.csv", index=False)

# ---- Q2  highest / lowest percentage returns -------------------------------
cols = ["symbol", "first_date", "first_close", "last_close", "raw_period_return_pct",
        "adj_period_return_pct", "extreme_move_days"]
q2 = full.sort_values("adj_period_return_pct", ascending=False)[cols]
q2.head(15).to_csv(u.OUT / "q2_top15_period_returns.csv", index=False)
q2.tail(15).sort_values("adj_period_return_pct").to_csv(u.OUT / "q2_bottom15_period_returns.csv", index=False)
q2.to_csv(u.OUT / "q2_all_full_history_returns.csv", index=False)

# ---- Q3  volatility ----------------------------------------------------------
q3 = full.sort_values("annualised_volatility_pct", ascending=False)[
    ["symbol", "daily_volatility_pct", "annualised_volatility_pct", "avg_daily_return_pct"]]
q3.head(15).to_csv(u.OUT / "q3_top15_volatility.csv", index=False)
q3.tail(15).sort_values("annualised_volatility_pct").to_csv(u.OUT / "q3_bottom15_volatility.csv", index=False)

# ---- Q4  trading volume ------------------------------------------------------
q4 = summ.sort_values("avg_volume", ascending=False)[["symbol", "avg_volume", "max_volume"]]
q4.head(15).to_csv(u.OUT / "q4_top15_avg_volume.csv", index=False)
top_vol_days = df.nlargest(15, "volume")[["symbol", "date", "close", "volume"]]
top_vol_days.to_csv(u.OUT / "q4_top15_single_day_volume.csv", index=False)

# ---- Q5  selected stocks 2014 -> 2017 (yearly performance) -------------------
rows = []
for s in sel:
    d = df[df.symbol == s].sort_values("date")
    yr_end = d.groupby("year")["close"].last()
    yr_start_ref = pd.concat([pd.Series([d["close"].iloc[0]], index=[2013]), yr_end])  # 2014 starts at first close
    rec = {"symbol": s}
    for y in range(2014, 2018):
        rec[f"return_{y}_pct"] = (yr_end[y] / yr_start_ref[y - 1] - 1) * 100
    rec["close_2014-01-02"] = d["close"].iloc[0]
    rec["close_2017-12-29"] = d["close"].iloc[-1]
    rec["total_return_pct"] = (d["close"].iloc[-1] / d["close"].iloc[0] - 1) * 100
    rows.append(rec)
q5 = pd.DataFrame(rows)
q5.to_csv(u.OUT / "q5_selected_yearly_returns.csv", index=False, float_format="%.2f")

# ---- Q6  variation across months and years -----------------------------------
# per-symbol monthly compounded (clean) return, then equal-weight average across full-history symbols
fd = df[df.symbol.isin(full.symbol)].copy()
fd["f"] = 1 + fd["daily_return_clean_pct"].fillna(0) / 100
m = fd.groupby(["symbol", "year", "month"])["f"].prod().sub(1).mul(100).rename("monthly_return_pct").reset_index()
mm = m.groupby(["year", "month"])["monthly_return_pct"].mean().reset_index()
mm.to_csv(u.OUT / "q6_equal_weight_monthly_return.csv", index=False, float_format="%.4f")
heat = mm.pivot(index="year", columns="month", values="monthly_return_pct")
heat.to_csv(u.OUT / "q6_monthly_return_heatmap_table.csv", float_format="%.3f")
avg_month = mm.groupby("month")["monthly_return_pct"].mean()
selmonth = (df[df.symbol.isin(sel)].groupby(["year_month", "symbol"])["close"].mean().unstack())
selmonth.to_csv(u.OUT / "q6_selected_monthly_avg_close.csv", float_format="%.4f")

# ---- Q7  largest daily price changes ------------------------------------------
ok = df[~df.extreme_move]
q7_usd = ok.assign(abs_change=ok["daily_change"].abs()).nlargest(15, "abs_change")[
    ["symbol", "date", "close", "daily_change", "daily_return_pct"]]
q7_gain = ok.nlargest(15, "daily_return_pct")[["symbol", "date", "close", "daily_return_pct", "volume"]]
q7_loss = ok.nsmallest(15, "daily_return_pct")[["symbol", "date", "close", "daily_return_pct", "volume"]]
q7_usd.to_csv(u.OUT / "q7_largest_dollar_changes.csv", index=False)
q7_gain.to_csv(u.OUT / "q7_largest_pct_gains.csv", index=False)
q7_loss.to_csv(u.OUT / "q7_largest_pct_losses.csv", index=False)

# ---- Q8  trading activity across selected symbols ----------------------------
v = df[(df.symbol.isin(sel)) & (df.volume > 0)].groupby("symbol")["volume"]
q8 = pd.DataFrame({"avg_volume": v.mean(), "median_volume": v.median(), "std_volume": v.std(),
                   "min_volume": v.min(), "max_volume": v.max()})
q8["volume_cv"] = q8["std_volume"] / q8["avg_volume"]
q8 = q8.loc[sel].reset_index()
q8.to_csv(u.OUT / "q8_selected_volume_stats.csv", index=False, float_format="%.2f")

# ---- Task 4  comparative analysis of the selected stocks ----------------------
rows = []
for s in sel:
    d = df[df.symbol == s].sort_values("date")
    r = d["daily_return_clean_pct"].dropna()
    last = d.iloc[-1]
    rows.append(dict(
        symbol=s,
        total_return_pct=(d.close.iloc[-1] / d.close.iloc[0] - 1) * 100,
        mean_daily_return_pct=r.mean(), median_daily_return_pct=r.median(),
        daily_volatility_pct=r.std(), annualised_volatility_pct=r.std() * np.sqrt(252),
        return_per_unit_risk=(r.mean() / r.std()) * np.sqrt(252),
        skewness=stats.skew(r), excess_kurtosis=stats.kurtosis(r),
        best_day_pct=r.max(), worst_day_pct=r.min(),
        highest_close=d.close.max(), highest_close_date=d.loc[d.close.idxmax(), "date"].date(),
        lowest_close=d.close.min(), lowest_close_date=d.loc[d.close.idxmin(), "date"].date(),
        avg_volume=d.loc[d.volume > 0, "volume"].mean(),
        avg_daily_range=d["daily_range"].mean(), avg_daily_range_pct=d["daily_range_pct"].mean(),
        pct_days_close_above_ma50=(d.loc[d.ma_50.notna(), "close"] > d.loc[d.ma_50.notna(), "ma_50"]).mean() * 100,
        latest_ma5=last.ma_5, latest_ma20=last.ma_20, latest_ma50=last.ma_50,
        ma20_vs_ma50_at_end="MA20 above MA50 (bullish trend)" if last.ma_20 > last.ma_50 else "MA20 below MA50 (bearish trend)",
    ))
comp = pd.DataFrame(rows)
comp.to_csv(u.OUT / "task4_comparative_stock_table.csv", index=False, float_format="%.4f")

# daily-return correlation between selected stocks and volume-vs-movement relationship
wide = df[df.symbol.isin(sel)].pivot(index="date", columns="symbol", values="daily_return_clean_pct")[sel]
wide.corr().to_csv(u.OUT / "task4_return_correlation_matrix.csv", float_format="%.4f")
vv = []
for s in sel:
    d = df[(df.symbol == s) & (df.volume > 0)].dropna(subset=["abs_return_pct"])
    rho, p = stats.spearmanr(d["volume"], d["abs_return_pct"])
    vv.append(dict(symbol=s, spearman_volume_vs_abs_return=rho, p_value=p, n=len(d)))
pd.DataFrame(vv).to_csv(u.OUT / "task4_volume_vs_abs_return.csv", index=False, float_format="%.4f")

# market-wide: equal-weight index of full-history stocks (event-adjusted, base 100)
ew = fd.groupby("date")["daily_return_clean_pct"].mean().fillna(0)
mkt = pd.DataFrame({"equal_weight_index": (1 + ew / 100).cumprod() * 100})
mkt.to_csv(u.OUT / "market_equal_weight_index.csv", float_format="%.4f")

# ---- print headline results (used when writing the report) -----------------------
pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
print("Q1 high:\n", q1_hi.head(5).to_string(index=False)); print("Q1 low:\n", q1_lo.head(5).to_string(index=False))
print("\nQ2 top:\n", q2.head(8).to_string(index=False)); print("Q2 bottom:\n", q2.tail(8).iloc[::-1].to_string(index=False))
print("\nQ3 top vol:\n", q3.head(8).to_string(index=False)); print("Q3 lowest:\n", q3.tail(5).iloc[::-1].to_string(index=False))
print("\nQ4 avg vol:\n", q4.head(6).to_string(index=False)); print(top_vol_days.head(5).to_string(index=False))
print("\nQ5:\n", q5.to_string(index=False))
print("\nQ6 heat:\n", heat.round(2).to_string()); print("avg by month:\n", avg_month.round(2).to_string())
print("\nQ7 gains:\n", q7_gain.head(5).to_string(index=False)); print(q7_loss.head(5).to_string(index=False)); print(q7_usd.head(5).to_string(index=False))
print("\nQ8:\n", q8.to_string(index=False))
print("\nTask4:\n", comp[["symbol", "total_return_pct", "annualised_volatility_pct", "return_per_unit_risk", "pct_days_close_above_ma50", "ma20_vs_ma50_at_end"]].to_string(index=False))
print("\ncorr:\n", wide.corr().round(2).to_string())
print("\nvol vs abs ret:\n", pd.DataFrame(vv).round(3).to_string(index=False))
print("\nEW index end:", mkt.iloc[-1, 0].round(1), "| full-history symbols:", len(full))
print("median full-history return:", full.adj_period_return_pct.median().round(1), "| share positive:", (full.adj_period_return_pct > 0).mean().round(3))
