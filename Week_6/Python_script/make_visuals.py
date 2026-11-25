"""
04_make_visuals.py - static analytical visualisations (PNG) for the report/README.
(The interactive visuals are in 04_PowerBI and 05_Plotly_Dashboard.)
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import sp500_utils as u

u.VIS.mkdir(exist_ok=True)
df = pd.read_csv(u.PROCESSED / "sp500_clean_full.csv", parse_dates=["date"])
summ = pd.read_csv(u.PROCESSED / "symbol_summary.csv", parse_dates=["first_date", "last_date"])
sel = u.SELECTED
full = summ[summ.history_status == "Full period"]
sd = df[df.symbol.isin(sel)]
PAL = dict(zip(sel, plt.cm.tab10.colors))
sns.set_theme(style="whitegrid", font_scale=0.95)
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(u.VIS / name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


# 01 cumulative performance, base 100 --------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))
for s in sel:
    d = sd[sd.symbol == s]
    ax.plot(d.date, 100 * d.close / d.close.iloc[0], label=s, color=PAL[s], lw=1.4)
ax.set_yscale("log"); ax.set_yticks([50, 100, 200, 500, 1000]); ax.set_yticklabels(["50", "100", "200", "500", "1,000"])
ax.axhline(100, color="grey", lw=.8, ls="--")
ax.set_title("Growth of 100 invested at the first close (2 Jan 2014) - selected stocks, log scale")
ax.set_ylabel("Index (start = 100)"); ax.legend(ncol=5, frameon=False, loc="upper left")
save(fig, "01_selected_cumulative_performance.png")

# 02 total return bars -----------------------------------------------------------------
t = summ[summ.symbol.isin(sel)].sort_values("adj_period_return_pct")
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(t.symbol, t.adj_period_return_pct, color=["#c0392b" if v < 0 else "#2a6f97" for v in t.adj_period_return_pct])
for i, v in enumerate(t.adj_period_return_pct):
    ax.text(v + (15 if v >= 0 else -15), i, f"{v:,.0f}%", va="center", ha="left" if v >= 0 else "right", fontsize=9)
ax.axvline(0, color="black", lw=.8)
ax.set_title("Total price return, 2 Jan 2014 - 29 Dec 2017 (unadjusted for dividends)")
ax.set_xlabel("Price return (%)"); ax.set_xlim(t.adj_period_return_pct.min() - 120, t.adj_period_return_pct.max() * 1.12)
save(fig, "02_selected_total_return.png")

# 03 risk vs return, all full-history stocks ------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(full.annualised_volatility_pct, full.adj_period_return_pct, s=14, color="#b0b7c3", alpha=.7, label="Other full-history stocks")
ss = full[full.symbol.isin(sel)]
ax.scatter(ss.annualised_volatility_pct, ss.adj_period_return_pct, s=60, color="#2a6f97", label="Selected stocks", zorder=3)
for _, r in ss.iterrows():
    ax.annotate(r.symbol, (r.annualised_volatility_pct, r.adj_period_return_pct), xytext=(5, 4), textcoords="offset points", fontsize=9)
ax.axhline(0, color="black", lw=.7)
ax.set_xlabel("Annualised volatility (%)"); ax.set_ylabel("Total price return 2014-2017 (%)")
ax.set_title("Return vs volatility - 483 stocks with a full-period history"); ax.legend(frameon=False)
save(fig, "03_risk_return_scatter.png")

# 04 return distributions ---------------------------------------------------------------------
fig, axes = plt.subplots(2, 5, figsize=(15, 6), sharex=True)
for ax, s in zip(axes.ravel(), sel):
    r = sd[sd.symbol == s]["daily_return_clean_pct"].dropna()
    ax.hist(r, bins=np.arange(-8, 8.01, .5), color=PAL[s], alpha=.85)
    ax.axvline(r.mean(), color="black", lw=1, ls="--")
    ax.set_title(f"{s}  (mean {r.mean():.2f}%, sd {r.std():.2f}%)", fontsize=9)
fig.suptitle("Distribution of daily % returns (dashed line = mean)", y=1.02)
for ax in axes[-1]: ax.set_xlabel("Daily return (%)")
save(fig, "04_return_distributions.png")

# 05 monthly return heatmap ---------------------------------------------------------------------
heat = pd.read_csv(u.OUT / "q6_monthly_return_heatmap_table.csv", index_col=0)
heat.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig, ax = plt.subplots(figsize=(10, 3.8))
sns.heatmap(heat, annot=True, fmt=".1f", cmap="RdBu", center=0, cbar_kws={"label": "Avg monthly return (%)"}, ax=ax, linewidths=.5)
ax.set_title("Equal-weight average monthly return across 483 full-history stocks (%)"); ax.set_ylabel("")
save(fig, "05_monthly_return_heatmap.png")

# 06 correlation heatmap ------------------------------------------------------------------------------
corr = pd.read_csv(u.OUT / "task4_return_correlation_matrix.csv", index_col=0)
fig, ax = plt.subplots(figsize=(7.5, 6))
mask = np.triu(np.ones_like(corr, dtype=bool), 1)
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=.7, ax=ax, linewidths=.5)
ax.set_title("Correlation of daily returns - selected stocks")
save(fig, "06_return_correlation.png")

# 07 trading volume --------------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
q8 = pd.read_csv(u.OUT / "q8_selected_volume_stats.csv").sort_values("avg_volume")
axes[0].barh(q8.symbol, q8.avg_volume / 1e6, color="#2a6f97")
axes[0].set_title("Average daily trading volume (million shares)"); axes[0].set_xlabel("Million shares")
mv = (sd[sd.volume > 0].groupby(["year_month", "symbol"])["volume"].mean().unstack() / 1e6)
mv.index = pd.to_datetime(mv.index + "-01")
for s in ["AAPL", "MSFT", "JPM", "XOM", "NFLX"]:
    axes[1].plot(mv.index, mv[s], label=s, color=PAL[s], lw=1.4)
axes[1].set_title("Monthly average volume (million shares)"); axes[1].legend(frameon=False, ncol=3)
save(fig, "07_trading_volume.png")

# 08 volume vs absolute return -------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
d = sd[(sd.symbol == "AAPL") & (sd.volume > 0)].dropna(subset=["abs_return_pct"])
axes[0].scatter(d.volume / 1e6, d.abs_return_pct, s=10, alpha=.5, color="#2a6f97")
rho, _ = stats.spearmanr(d.volume, d.abs_return_pct)
axes[0].set_xscale("log"); axes[0].set_xlabel("Daily volume (million shares, log)"); axes[0].set_ylabel("|Daily return| (%)")
axes[0].set_title(f"AAPL: volume vs size of daily move (Spearman rho = {rho:.2f})")
vv = pd.read_csv(u.OUT / "task4_volume_vs_abs_return.csv").sort_values("spearman_volume_vs_abs_return")
axes[1].barh(vv.symbol, vv.spearman_volume_vs_abs_return, color="#2a6f97")
axes[1].set_title("Spearman correlation: volume vs |daily return|"); axes[1].set_xlim(0, .6)
save(fig, "08_volume_vs_price_movement.png")

# 09 moving averages ----------------------------------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, s in zip(axes.ravel(), ["AAPL", "AMZN", "XOM", "NVDA"]):
    d = sd[sd.symbol == s]
    ax.plot(d.date, d.close, color="#9aa5b1", lw=1, label="Close")
    ax.plot(d.date, d.ma_5, color="#e69f00", lw=1, label="MA 5")
    ax.plot(d.date, d.ma_20, color="#2a6f97", lw=1.2, label="MA 20")
    ax.plot(d.date, d.ma_50, color="#c0392b", lw=1.4, label="MA 50")
    ax.set_title(s); ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper left")
fig.suptitle("Closing price and moving averages (5 / 20 / 50 trading days)", y=1.0)
save(fig, "09_moving_averages.png")

# 10 rolling volatility ---------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5))
for s in sel:
    d = sd[sd.symbol == s]
    ax.plot(d.date, d.rolling_vol_20 * np.sqrt(252), label=s, color=PAL[s], lw=1.1)
ax.set_ylabel("20-day rolling volatility (annualised %)"); ax.legend(ncol=5, frameon=False, loc="upper left")
ax.set_title("Rolling 20-day volatility - selected stocks")
save(fig, "10_rolling_volatility.png")

# 11 market leaders panel ---------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
h = summ.nlargest(10, "max_close").sort_values("max_close")
axes[0].barh(h.symbol, h.max_close, color="#2a6f97"); axes[0].set_title("Highest closing price per stock (USD*)")
r = full.nlargest(10, "adj_period_return_pct").sort_values("adj_period_return_pct")
axes[1].barh(r.symbol, r.adj_period_return_pct, color="#2d936c"); axes[1].set_title("Highest 2014-17 price return (%)")
v = full.nlargest(10, "annualised_volatility_pct").sort_values("annualised_volatility_pct")
axes[2].barh(v.symbol, v.annualised_volatility_pct, color="#c0392b"); axes[2].set_title("Highest annualised volatility (%)")
fig.text(0.01, -0.02, "*Currency not stated in the dataset; USD assumed (US-listed stocks).", fontsize=8)
save(fig, "11_market_leaders.png")

# 12 dataset coverage -----------------------------------------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
axes[0].hist(summ.trading_days, bins=40, color="#2a6f97")
axes[0].set_title("Trading days per symbol (1,007 = complete)"); axes[0].set_xlabel("Trading days"); axes[0].set_ylabel("Symbols")
c = df.groupby("year").size()
axes[1].bar(c.index.astype(str), c.values, color="#2a6f97")
for x, y in zip(c.index.astype(str), c.values): axes[1].text(x, y, f"{y:,}", ha="center", va="bottom", fontsize=9)
axes[1].set_title("Records per year"); axes[1].set_ylim(0, c.max() * 1.1)
save(fig, "12_dataset_coverage.png")

# 13 OHLC monthly averages (AAPL) ---------------------------------------------------------------------------------------------------
d = sd[sd.symbol == "AAPL"].groupby("year_month")[["open", "high", "low", "close"]].mean()
d.index = pd.to_datetime(d.index + "-01")
fig, ax = plt.subplots(figsize=(11, 4.8))
for c_, col in zip(["high", "close", "open", "low"], ["#2d936c", "#2a6f97", "#e69f00", "#c0392b"]):
    ax.plot(d.index, d[c_], label=c_.title(), color=col, lw=1.5)
ax.set_title("AAPL - monthly average open, high, low and close"); ax.legend(frameon=False, ncol=4)
save(fig, "13_aapl_ohlc_monthly.png")
