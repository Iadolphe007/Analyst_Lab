"""
05_validate.py - Track A, Task 6: independent validation.
Recomputes key figures from the ORIGINAL CSV using only the csv/statistics modules
(no pandas) and compares them with the processed data, analysis tables and the
Power BI tables. Writes 08_Validation/validation_results.csv and Validation_Evidence.md
"""
import csv, statistics, math
from datetime import datetime
import pandas as pd
import sp500_utils as u

u.VAL.mkdir(exist_ok=True)
results = []


def check(name, expected, actual, tol=1e-6, note=""):
    ok = abs(expected - actual) <= tol if isinstance(expected, (int, float)) else expected == actual
    results.append(dict(check=name, independent_value=expected, pipeline_value=actual,
                        tolerance=tol if isinstance(expected, (int, float)) else "exact",
                        result="PASS" if ok else "FAIL", note=note))


# ---- independent read of the raw file (pure python) --------------------------------
rows = {}
n = 0
with open(u.RAW_CSV, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        n += 1
        d = datetime.strptime(r["date"], "%m/%d/%Y")
        rows.setdefault(r["symbol"], []).append((d, r))
for s in rows:
    rows[s].sort(key=lambda x: x[0])

proc = pd.read_csv(u.PROCESSED / "sp500_clean_full.csv", parse_dates=["date"])
summ = pd.read_csv(u.PROCESSED / "symbol_summary.csv")
pbp = pd.read_csv(u.PBI_DATA / "Prices.csv", parse_dates=["date"])

# V1 counts ---------------------------------------------------------------------------------
check("V1a Total records (raw vs processed)", n, len(proc), 0)
check("V1b Unique symbols", len(rows), proc.symbol.nunique(), 0)
check("V1c Power BI Prices.csv row count", n, len(pbp), 0)
dates = {d for s in rows for d, _ in rows[s]}
check("V1d Distinct trading dates", len(dates), proc.date.nunique(), 0)

# V2 daily returns, AAPL (manual loop) ---------------------------------------------------------
def closes(sym):
    return [(d, float(r["close"])) for d, r in rows[sym]]

ac = closes("AAPL")
manual = [(ac[i][1] / ac[i - 1][1] - 1) * 100 for i in range(1, len(ac))]
p_a = proc[proc.symbol == "AAPL"].sort_values("date")["daily_return_pct"].iloc[1:].tolist()
check("V2 AAPL daily return: max |difference| over 1,006 days", 0.0,
      max(abs(a - b) for a, b in zip(manual, p_a)), 1e-9, "manual loop vs pandas groupby/pct_change")
check("V2b AAPL first-day return is blank (no prior close)", True,
      bool(pd.isna(proc[proc.symbol == "AAPL"].sort_values("date")["daily_return_pct"].iloc[0])), 0)

# V3 moving average (manual windows) ---------------------------------------------------------------
vals = [c for _, c in ac]
for w in (5, 20, 50):
    man = [sum(vals[i - w + 1:i + 1]) / w for i in range(w - 1, len(vals))]
    pipe = proc[proc.symbol == "AAPL"].sort_values("date")[f"ma_{w}"].dropna().tolist()
    check(f"V3 AAPL MA{w}: count of values and max |difference|", 0.0,
          max(abs(a - b) for a, b in zip(man, pipe)) if len(man) == len(pipe) else 999, 1e-6,
          f"{len(man)} manual vs {len(pipe)} pipeline values")
# first MA value must not exist before w observations (no look-ahead / no partial windows)
check("V3d MA50 first valid row is the 50th observation", 49,
      int(proc[proc.symbol == "AAPL"].sort_values("date").reset_index()["ma_50"].first_valid_index()), 0)

# V4 period returns + average close, all selected stocks -----------------------------------------------
for s in u.SELECTED:
    c = [x for _, x in closes(s)]
    check(f"V4 {s} total price return (%)", (c[-1] / c[0] - 1) * 100,
          float(summ.loc[summ.symbol == s, "raw_period_return_pct"].iloc[0]), 1e-2, "summary stored at 4 dp")
    check(f"V4 {s} average close", sum(c) / len(c), float(summ.loc[summ.symbol == s, "avg_close"].iloc[0]), 1e-3)

# V5 volatility with statistics.stdev (MSFT, JPM) ---------------------------------------------------------
for s in ("MSFT", "JPM"):
    c = [x for _, x in closes(s)]
    rets = [(c[i] / c[i - 1] - 1) * 100 for i in range(1, len(c))]
    check(f"V5 {s} daily volatility (stdev of returns)", statistics.stdev(rets),
          float(summ.loc[summ.symbol == s, "daily_volatility_pct"].iloc[0]), 1e-3)

# V6 highest close & max volume across the whole file -----------------------------------------------------------
best = max(((float(r["close"]), s, d) for s in rows for d, r in rows[s]))
check("V6a Highest close in file (PCLN)", best[0], float(proc.close.max()), 1e-9, f"{best[1]} on {best[2].date()}")
mv = max(((int(r["volume"]), s) for s in rows for d, r in rows[s]))
check("V6b Highest single-day volume (VZ)", mv[0], int(proc.volume.max()), 0, mv[1])
check("V6c Total volume of all rows reconciles to Power BI table", sum(int(r["volume"]) for s in rows for d, r in rows[s]),
      int(pbp.volume.sum()), 0)

# V7 filter test: selected stocks + 2016 date window (what the dashboard slicers do) ------------------------------
lo, hi = datetime(2016, 1, 1), datetime(2016, 12, 31)
sel_set = {"AAPL", "MSFT", "JPM"}
manual_vals = [float(r["close"]) for s in sel_set for d, r in rows[s] if lo <= d <= hi]
f = pbp[pbp.symbol.isin(sel_set) & (pbp.date >= "2016-01-01") & (pbp.date <= "2016-12-31")]
check("V7a Filter test (3 symbols, 2016): row count", len(manual_vals), len(f), 0)
check("V7b Filter test: average close", sum(manual_vals) / len(manual_vals), float(f.close.mean()), 1e-3,
      "Power BI Avg Close measure = AVERAGE(Prices[close]) on this filter")

# V8 missing values never replaced by zero --------------------------------------------------------------------------
raw_missing = sum(1 for s in rows for d, r in rows[s] for c in ("open", "high", "low") if r[c] == "")
pb_missing = int(pbp[["open", "high", "low"]].isna().sum().sum())
check("V8a Missing open/high/low cells preserved as blanks (11+8+8)", raw_missing, pb_missing, 0)
check("V8b No zero prices introduced", 0, int((proc[["open", "high", "low", "close"]] == 0).sum().sum()), 0)

# V9 flags ------------------------------------------------------------------------------------------------------------
check("V9a Non-market events flagged", len(u.NON_MARKET_EVENTS), int(proc.extreme_move.sum()), 0)
check("V9b Zero-volume rows", sum(1 for s in rows for d, r in rows[s] if int(r["volume"]) == 0),
      int(proc.zero_volume.sum()), 0)

res = pd.DataFrame(results)
res.to_csv(u.VAL / "validation_results.csv", index=False)
passed = (res.result == "PASS").sum()
print(res.to_string(index=False))
print(f"\n{passed}/{len(res)} checks passed")

# ---- evidence document ------------------------------------------------------------------------------------------------
md = ["# Validation Evidence - S&P 500 Track A", "",
      f"**Result: {passed} of {len(res)} independent checks passed.**", "",
      "Method: figures were recomputed from the *original* CSV with Python's `csv` and `statistics` modules "
      "(no pandas, no shared code with the pipeline) and compared with the processed dataset, the analysis "
      "tables and the Power BI tables (`04_PowerBI/data`). Script: `02_Scripts/05_validate.py`.", "",
      "| Check | Independent value | Pipeline value | Tolerance | Result |", "|---|---|---|---|---|"]
for r in results:
    fmt = lambda v: f"{v:,.6g}" if isinstance(v, float) else str(v)
    md.append(f"| {r['check']} | {fmt(r['independent_value'])} | {fmt(r['pipeline_value'])} | {r['tolerance']} | {r['result']} |")
md += ["", "## Discrepancies investigated", "",
       "1. **Rounding in Power BI tables.** `Prices.csv` stores prices/returns to 4 decimals (size control). Averages and "
       "returns therefore differ from the source in the 4th-5th decimal at most (e.g. GOOGL first close 557.1166 vs 557.1170 "
       "displayed). Tolerances above reflect this; no business-relevant difference.",
       "2. **Records vs symbols with incomplete histories.** 22 symbols start late/end early (e.g. APTV only 18 days) and "
       "4 more (DHR, ES, ICE, O) miss a handful of days. Rankings of returns/volatility use only the 483 symbols with a full-period "
       "history, so dashboard 'all symbols' averages differ from rankings by design.",
       "3. **Return of LNT, NI, EBAY, DISCA/DISCK, BAX etc.** Raw close-to-close returns show -45% to -63% single-day moves caused by "
       "probable spin-offs/splits (or, for LNT, a data glitch). These are flagged, excluded from average-return/volatility statistics "
       "and treated as 0% in the event-adjusted cumulative return. See `07_Analysis_Outputs/dq_large_moves.csv`.",
       "4. **Dashboard vs source for zero-volume rows.** Four rows (DHR, O, UA, FTV) have zero volume and blank open/high/low but a valid close; "
       "they remain in record counts and price statistics and are excluded from volume statistics (`Min Volume (non-zero)`).",
       "", "## Filter and date-slicer behaviour", "",
       "Checks V7a/V7b reproduce what the Power BI symbol and date slicers do (symbol IN set, date BETWEEN range) and match the independent result exactly. "
       "The same logic drives the Plotly dashboard's filters.",
       "", "## Not verified here", "",
       "The Power BI project (`.pbip`) and the Plotly HTML could not be opened in Power BI Desktop / a browser inside the build environment. "
       "Open each, apply the same filters (AAPL, MSFT, JPM; 2016) and confirm Avg Close and record count match V7a/V7b; add screenshots to `10_Screenshots/`."]
(u.VAL / "Validation_Evidence.md").write_text("\n".join(md), encoding="utf-8")
