"""
08_build_notebook.py - builds 03_Notebook/SP500_Track_A_Data_Analytics.ipynb and EXECUTES every
code cell (jupyter is not required): stdout and matplotlib figures are captured into the notebook
outputs, so the .ipynb opens with results already shown. Re-run the notebook in Jupyter to refresh.
"""
import io, sys, json, base64, contextlib, traceback
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sp500_utils as u

cells = []
md = lambda s: cells.append(("markdown", s.strip("\n")))
code = lambda s: cells.append(("code", s.strip("\n")))

md("""
# S&P 500 Stock Market Performance and Business Intelligence - Track A (Data Analytics)
**AnalystLab Africa - Experience Lab Internship - Week 6** &nbsp;|&nbsp; Dataset: `S&P 500 Stock Prices 2014-2017.csv`

**Business problem.** Financial researchers need to understand how individual stocks behaved between 2014 and 2017: which delivered the highest
returns, which were most volatile, how trading activity varied and how volume relates to price moves. Raw prices alone mislead
(a $2,000 stock is not "better" than a $50 stock), so the analysis is built on **percentage returns, volatility and volume**, validated independently.

**Intended users:** equity research analysts and market-intelligence teams. **Decisions supported:** which stocks to study further, how to compare
risk/return, where data needs correcting before reporting. **Important:** all results are *historical (2014-2017)*; they are not current market data and not investment advice.

**Success criteria** (Task 3 of the common requirements)
1. Key figures reconcile with an independent pure-Python recomputation from the raw CSV (target: 100% of checks pass).
2. Every ranking uses percentage returns/volatility on a comparable (full-period) stock set, with data-quality exclusions documented.
3. The dashboards (Power BI + Plotly) expose the 4 required pages with symbol and date filters, and their filtered results match the source.
4. At least 5 findings and 3 recommendations, each with supporting evidence.
""")
code("""
import sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "../02_Scripts")
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
import sp500_utils as u
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30)
sns.set_theme(style="whitegrid")
raw = pd.read_csv(u.RAW_CSV, encoding="utf-8-sig")      # original file, never modified
print("Original file loaded:", raw.shape)
""")
md("## 1. Inspect the data (Task 1)")
code("""
print("Columns :", list(raw.columns))
print(raw.dtypes.to_string())
print("\\nFirst rows:"); print(raw.head(3).to_string(index=False))
df0 = u.load_raw()                                       # only change: date text (M/D/YYYY) -> datetime
print("\\nRecords:", len(df0), "| Symbols:", df0.symbol.nunique(), "| Trading dates:", df0.date.nunique())
print("Date range:", df0.date.min().date(), "to", df0.date.max().date())
print("\\nMissing values:\\n", raw.isna().sum().to_string())
print("\\nDuplicate symbol-date pairs:", df0.duplicated(["symbol","date"]).sum())
print("Zero-volume rows:", (df0.volume == 0).sum())
print("File sorted by symbol/date already?", df0.equals(df0.sort_values(["symbol","date"]).reset_index(drop=True)))
""")
code("""
print("Rows with missing open/high/low:"); print(df0[df0[["open","high","low"]].isna().any(axis=1)].to_string(index=False))
print("\\nZero-volume rows:"); print(df0[df0.volume == 0].to_string(index=False))
""")
code("""
cnt = df0.groupby("symbol").agg(first=("date","min"), last=("date","max"), days=("date","count"))
inc = cnt[cnt.days < df0.date.nunique()].sort_values("days")
print(f"{len(inc)} symbols have fewer than {df0.date.nunique()} records. Examples (shortest histories):")
print(inc.head(8).to_string())
print("\\nHighest close :", df0.loc[df0.close.idxmax(), ["symbol","date","close"]].tolist())
print("Lowest close  :", df0.loc[df0.close.idxmin(), ["symbol","date","close"]].tolist())
print("Highest volume:", df0.loc[df0.volume.idxmax(), ["symbol","date","volume"]].tolist())
""")
md("""
**Data-quality findings.** All figures in the assignment brief were confirmed: 11/8/8 missing open/high/low, no duplicates, 4 zero-volume rows (these also have blank O/H/L but a valid close),
and 26 symbols with incomplete histories (22 start late/end early). Further issues found: dates are text in `M/D/YYYY`; the file is not sorted by symbol-date; 9 rows have logically inconsistent OHLC values;
and a screen of every daily move above 25% (39 cases) shows some drops are almost certainly **spin-offs/splits/special dividends** (e.g. EBAY -57% when PayPal was spun off) because the file has no adjusted close.
""")
md("## 2. Cleaning and preparation (Task 2)")
code("""
df = u.prepare(df0)
new_cols = [c for c in df.columns if c not in raw.columns]
print("Engineered fields:", new_cols)
print("\\nNon-market events excluded from return statistics (analyst-judgement list; verify with vendor):")
for (s, d), note in u.NON_MARKET_EVENTS.items(): print(f"  {s:6s} {d}  {note}")
print("\\nLarge moves >25% retained as genuine market moves:", int(df.large_move.sum()))
print("OHLC-inconsistent rows flagged:", int(df.ohlc_inconsistent.sum()))
print(df[df.symbol == "AAPL"][["date","close","daily_change","daily_return_pct","daily_range","ma_5","ma_20","ma_50"]].iloc[[0,1,5,25,60]].to_string(index=False))
""")
md("""
**Decisions.** (1) Missing O/H/L are left blank - never zero-filled; (2) zero-volume rows stay (valid close) but are excluded from volume statistics;
(3) every calculation is per symbol on date-sorted data; moving averages need a full window (no partial windows, no look-ahead);
(4) the 13 flagged non-market days are excluded from average-return / volatility and count as 0% in the event-adjusted cumulative return.
""")
code("""
summ = u.symbol_summary(df)
full = summ[summ.history_status == "Full period"]
print("Symbols with a full-period history (used for rankings):", len(full), "of", len(summ))
SEL = u.SELECTED; print("Selected stocks:", SEL)
""")
md("## 3. Market performance analysis (Task 3 - all 8 questions)")
md("### Q1. Which stocks recorded the highest (and lowest) closing prices?\n*Method: maximum / minimum `close` per symbol.*")
code("""
print(summ.nlargest(8,"max_close")[["symbol","max_close","max_close_date"]].to_string(index=False))
print(); print(summ.nsmallest(5,"min_close")[["symbol","min_close","min_close_date"]].to_string(index=False))
""")
md("**Interpretation.** PCLN (Priceline) peaked at $2,049 and AMZN at $1,196, while CHK touched $1.59 and AMD $1.62 - but price *level* says nothing about performance; it mainly reflects share count/split history. Use returns (Q2).")
md("### Q2. Which stocks recorded the highest and lowest percentage returns?\n*Method: (last close / first close - 1) x 100, event-adjusted; full-period symbols only.*")
code("""
cols = ["symbol","first_close","last_close","raw_period_return_pct","adj_period_return_pct"]
print("Top 10:"); print(full.nlargest(10,"adj_period_return_pct")[cols].round(1).to_string(index=False))
print("\\nBottom 10:"); print(full.nsmallest(10,"adj_period_return_pct")[cols].round(1).to_string(index=False))
print("\\nMedian full-history return: %.1f%% | share of stocks with positive return: %.1f%%" % (full.adj_period_return_pct.median(), (full.adj_period_return_pct>0).mean()*100))
""")
md("**Interpretation.** NVDA (+1,120%), AVGO (+388%) and EA (+360%) led; the weakest were mostly energy names (CHK -85%, RRC -79%, NBL, NOV) hit by the 2014-16 oil-price fall. The typical stock gained ~49% and ~81% finished higher. Returns exclude dividends (price return only).")
md("### Q3. Which stocks experienced the greatest price volatility?\n*Method: standard deviation of clean daily % returns; annualised x sqrt(252).*")
code("""
v = full.sort_values("annualised_volatility_pct", ascending=False)[["symbol","daily_volatility_pct","annualised_volatility_pct","adj_period_return_pct"]]
print("Most volatile:"); print(v.head(8).round(2).to_string(index=False))
print("\\nLeast volatile:"); print(v.tail(5).iloc[::-1].round(2).to_string(index=False))
""")
md("**Interpretation.** Energy/mining and high-growth names (CHK 72%, AMD 62%, FCX 59%, WMB 51% annualised) were 4-5x as volatile as defensive staples (PEP, PG, KO, WM ~13-14%).")
md("### Q4. Which stocks recorded the highest trading volumes?\n*Method: mean daily volume (zero-volume rows excluded) and single-day maximum.*")
code("""
print(summ.nlargest(8,"avg_volume")[["symbol","avg_volume","max_volume"]].round(0).to_string(index=False))
print(); print(df.nlargest(5,"volume")[["symbol","date","close","volume"]].to_string(index=False))
""")
md("**Interpretation.** BAC (~89M shares/day), AAPL (~45M) and GE (~41M) were the most actively traded by share count. Volume counts *shares*, not money - low-priced stocks trade more shares.")
md("### Q5. How did the selected stocks perform between 2014 and 2017?")
code("""
q5 = pd.read_csv(u.OUT / "q5_selected_yearly_returns.csv").round(1)
print(q5.to_string(index=False))
fig, ax = plt.subplots(figsize=(11,5))
for s in SEL:
    d = df[df.symbol==s]; ax.plot(d.date, 100*d.close/d.close.iloc[0], label=s, lw=1.3)
ax.set_yscale("log"); ax.set_title("Growth of 100 (first close = 100), log scale"); ax.legend(ncol=5, frameon=False); plt.show()
""")
md("**Interpretation.** All but XOM finished above their 2014 start. 2015 was the standout year for AMZN (+118%) and NFLX (+134%) while WMT fell 29%; NVDA's +224% in 2016 drove its +1,120% total.")
md("### Q6. How did stock prices vary across months and years?\n*Method: per-stock compounded monthly return, averaged equally across 483 full-history stocks.*")
code("""
heat = pd.read_csv(u.OUT / "q6_monthly_return_heatmap_table.csv", index_col=0)
heat.columns = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
fig, ax = plt.subplots(figsize=(10,3.6)); sns.heatmap(heat, annot=True, fmt=".1f", cmap="RdBu", center=0, ax=ax); ax.set_title("Equal-weight avg monthly return (%)"); plt.show()
print("Average by calendar month (%):"); print(heat.mean().round(2).to_string())
""")
md("**Interpretation.** Aug-2015 (-5.5%) and Jan-2016 (-5.5%) were the weakest months; Oct-2015 (+7.2%) and Mar-2016 (+7.9%) the strongest. Feb/Oct/Nov averaged best and Jan/Aug/Sep worst, but with only four observations per month this is **not evidence of reliable seasonality**.")
md("### Q7. Which stocks experienced the largest daily price changes?")
code("""
ok = df[~df.extreme_move]
print("Largest daily $ changes:"); print(ok.assign(a=ok.daily_change.abs()).nlargest(5,"a")[["symbol","date","close","daily_change","daily_return_pct"]].round(2).to_string(index=False))
print("\\nLargest % gains:"); print(ok.nlargest(5,"daily_return_pct")[["symbol","date","close","daily_return_pct"]].round(1).to_string(index=False))
print("\\nLargest % losses:"); print(ok.nsmallest(5,"daily_return_pct")[["symbol","date","close","daily_return_pct"]].round(1).to_string(index=False))
""")
md("**Interpretation.** Dollar changes are dominated by the highest-priced stock (PCLN), so percentage moves are the fairer yardstick: AMD +52% (22 Apr 2016), WMB -35% (8 Feb 2016) and EVHC -34% (1 Nov 2017) were the biggest genuine one-day moves.")
md("### Q8. How does trading activity differ across the selected stocks?")
code("""
q8 = pd.read_csv(u.OUT / "q8_selected_volume_stats.csv")
print(q8.round(2).to_string(index=False))
""")
md("**Interpretation.** AAPL and MSFT trade tens of millions of shares daily; AMZN and GOOGL only 2-4 million because of their high share prices. NFLX (CV 0.77) and NVDA (0.71) had the most erratic volume.")
md("## 4. Comparative stock analysis (Task 4)")
code("""
comp = pd.read_csv(u.OUT / "task4_comparative_stock_table.csv")
show = ["symbol","total_return_pct","mean_daily_return_pct","annualised_volatility_pct","return_per_unit_risk","highest_close","lowest_close","avg_volume","pct_days_close_above_ma50"]
print(comp[show].round(2).to_string(index=False))
print("\\nMoving-average position at 29 Dec 2017:"); print(comp[["symbol","latest_ma5","latest_ma20","latest_ma50","ma20_vs_ma50_at_end"]].round(2).to_string(index=False))
""")
code("""
fig, axes = plt.subplots(2, 2, figsize=(14, 7))
for ax, s in zip(axes.ravel(), ["AAPL","AMZN","XOM","NVDA"]):
    d = df[df.symbol==s]
    ax.plot(d.date, d.close, color="#9aa5b1", lw=1, label="Close")
    for w, c in zip((5,20,50), ("#e69f00","#2a6f97","#c0392b")): ax.plot(d.date, d[f"ma_{w}"], color=c, lw=1.2, label=f"MA{w}")
    ax.set_title(s); ax.legend(ncol=4, frameon=False, fontsize=8)
plt.tight_layout(); plt.show()
""")
code("""
corr = df[df.symbol.isin(SEL)].pivot(index="date", columns="symbol", values="daily_return_clean_pct")[SEL].corr()
fig, ax = plt.subplots(figsize=(6.5,5)); sns.heatmap(corr, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=.7, ax=ax); ax.set_title("Daily-return correlation"); plt.show()
vv = pd.read_csv(u.OUT / "task4_volume_vs_abs_return.csv"); print(vv.round(3).to_string(index=False))
""")
md("""
**Interpretation.** On a risk-adjusted basis NVDA (return per unit of risk 1.85) led, followed by MSFT (1.07), AMZN (1.06) and NFLX (0.99); XOM was the only negative. Daily returns of the selected stocks are positively but moderately correlated (0.10-0.57;
GOOGL-AMZN 0.57, GOOGL-MSFT 0.55 highest; NVDA-WMT 0.10 lowest). Volume and the *size* of the daily move are positively related for every stock (Spearman 0.41-0.51): heavier trading accompanies bigger moves (association, not causation).
""")
md("## 5. Interactive dashboards (Task 5)")
md("""
Two interactive dashboards were built on the prepared data:
* **Power BI** - open `04_PowerBI/SP500_Dashboard.pbip` (4 pages: Market Overview, Stock Price Performance, Returns and Volatility, Trading Volume Analysis; symbol and date slicers). See `04_PowerBI/PowerBI_Setup_and_Manual_Build_Guide.md`.
* **Plotly** - open `05_Plotly_Dashboard/SP500_Interactive_Dashboard.html` (same 4 pages with symbol / date filters). The cell below shows the Plotly API version of one chart when `plotly` is installed.
""")
code("""
try:
    import plotly.express as px
    d = df[df.symbol.isin(SEL[:5])]
    px.line(d, x="date", y="close", color="symbol", title="Closing price - selected stocks").show()
except ImportError:
    print("plotly is not installed in this environment; the interactive Plotly dashboard is in 05_Plotly_Dashboard/ (HTML, loads Plotly.js from the CDN).")
""")
md("## 6. Validation (Task 6)")
code("""
val = pd.read_csv(u.VAL / "validation_results.csv")
print(val.result.value_counts().to_string())
print(val[["check","independent_value","pipeline_value","result"]].head(14).to_string(index=False))
print("... full table in 08_Validation/validation_results.csv")
""")
md("All 41 independent checks passed (record counts, AAPL daily returns, MA5/20/50, total returns, average closes, volatility, extremes, filter test and Power BI table reconciliation).")
md("## 7. Business insights and recommendations (Task 7)")
md("""
### Findings
1. **Leaders and laggards were sector-driven.** Technology/growth names led (NVDA +1,120%, AVGO +388%, EA +360%); energy led the losers (CHK -85%, RRC -79%). Median stock +49%, 81% positive.
2. **Price level is not performance.** PCLN's $2,049 peak and CHK's $1.59 low are share-price levels; rankings must use % returns (NVDA +1,120% vs PCLN far lower).
3. **Risk varies 5x across stocks.** CHK/AMD/FCX volatility of 59-72% vs ~13-14% for PEP/PG/KO; among selected stocks NFLX (42%) and NVDA (38%) were ~3x as volatile as JNJ (14%).
4. **Best risk-adjusted performer was NVDA** (1.85 return per unit of risk), well ahead of MSFT/AMZN (~1.06); XOM destroyed value (-16%) with moderate volatility.
5. **Volume rises with price-move size.** Spearman 0.41-0.51 (p<0.001) between volume and |daily return| for all 10 selected stocks.
6. **Diversification is visible in the data.** Selected-stock return correlations range 0.10-0.57; WMT/NVDA (0.10) and JNJ/NFLX (0.14) move most independently, GOOGL/AMZN (0.57) most together.
7. **Data limitations materially change results.** 13 non-market days (e.g. EBAY -57%, NI -63%) would corrupt returns/volatility if left in; 22 symbols have partial histories and cannot be ranked against full-period ones.

### Recommendations
| # | Recommendation | Evidence | How stakeholders use it |
|---|---|---|---|
| 1 | Obtain an adjusted-close/corporate-action feed (or verify flagged events) before publishing long-term returns | 13 flagged days with -35% to -63% one-day drops; 26 incomplete histories | Research team signs off return tables only after corporate actions are confirmed |
| 2 | Compare stocks with % return, volatility and return-per-risk together, never raw price | PCLN/CHK price extremes vs NVDA/CHK return extremes; NVDA 1.85 vs XOM -0.16 return per risk | Analysts shortlist stocks on risk-adjusted return and size positions by volatility |
| 3 | Use volume spikes as a screening flag for unusual price moves, and pair low-correlation stocks for diversification | Spearman 0.41-0.51 volume vs move size; correlations 0.10-0.57 | Monitoring desk flags days with heavy volume and large moves; portfolio researchers test WMT/NVDA-type pairs |

*Historical performance does not guarantee future returns. No predictive claims are made in this analysis.*
""")

# ---------------------------------------------------------------------------- execute & write
ns = {"__name__": "__main__"}
nb_cells, n = [], 0
for kind, src in cells:
    lines = src.split("\n")
    srcl = [l + "\n" for l in lines[:-1]] + [lines[-1]]
    if kind == "markdown":
        nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": srcl}); continue
    n += 1
    buf, outputs = io.StringIO(), []
    plt.close("all")
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, f"<cell {n}>", "exec"), ns)
    except Exception:
        buf.write("\n" + traceback.format_exc()); print("CELL ERROR", n); print(traceback.format_exc())
    if buf.getvalue():
        t = buf.getvalue().split("\n"); t = [x + "\n" for x in t[:-1]] + ([t[-1]] if t[-1] else [])
        outputs.append({"output_type": "stream", "name": "stdout", "text": t})
    for num in plt.get_fignums():
        b = io.BytesIO(); plt.figure(num).savefig(b, format="png", dpi=90, bbox_inches="tight")
        outputs.append({"output_type": "display_data", "metadata": {},
                        "data": {"image/png": base64.b64encode(b.getvalue()).decode(), "text/plain": ["<Figure>"]}})
    nb_cells.append({"cell_type": "code", "metadata": {}, "source": srcl, "execution_count": n, "outputs": outputs})
nb = {"cells": nb_cells, "nbformat": 4, "nbformat_minor": 5,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                   "language_info": {"name": "python", "version": "3.11"}}}
out = u.ROOT / "03_Notebook" / "SP500_Track_A_Data_Analytics.ipynb"
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("notebook written:", out.name, round(out.stat().st_size / 1e6, 2), "MB; code cells:", n)
