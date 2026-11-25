"""
09_build_docs.py - KPI definition sheet (xlsx), Data-quality assessment (docx), Executive summary (docx),
Power BI setup guide (md), README (md), requirements.txt, screenshots checklist.
"""
import json
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sp500_utils as u

DOCS = u.DOCS; DOCS.mkdir(exist_ok=True)
dq = json.load(open(u.OUT / "data_quality_summary.json"))
val = pd.read_csv(u.VAL / "validation_results.csv")
comp = pd.read_csv(u.OUT / "task4_comparative_stock_table.csv")
large = pd.read_csv(u.OUT / "dq_large_moves.csv")
inc = pd.read_csv(u.OUT / "dq_incomplete_histories.csv")
NAVY = "14324A"

# ============================================================================ KPI sheet
wb = Workbook()
hdr_fill = PatternFill("solid", fgColor=NAVY); hdr_font = Font(bold=True, color="FFFFFF")
thin = Side(style="thin", color="D0D7DE")


def sheet(ws, headers, rows, widths):
    ws.append(headers)
    for r in rows:
        ws.append(r)
    for c in ws[1]:
        c.fill = hdr_fill; c.font = hdr_font; c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = Border(bottom=thin)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"


kpis = [
    ["Total stock symbols", "Number of distinct tickers in the file", "DISTINCTCOUNT(symbol)", "Dataset", "Total Symbols", "505", "Includes 22 partial-history symbols; not all were S&P 500 members for the whole period."],
    ["Total trading records", "Number of symbol-date rows", "COUNTROWS(Prices)", "Dataset", "Total Records", "497,472", "One row per stock per trading date."],
    ["Date coverage", "First and last trading date", "MIN(date), MAX(date)", "Dataset", "Start Date / End Date", "2014-01-02 to 2017-12-29", "Historical only - not current market data."],
    ["Average closing price", "Mean of close over the selected symbols/dates", "AVERAGE(close)", "Selection", "Avg Close", "varies", "A price level, not a performance measure. Currency not in file (USD assumed)."],
    ["Highest / lowest close", "Max / min close in selection", "MAX(close), MIN(close)", "Symbol", "Max Close / Min Close", "PCLN 2,049.00 / CHK 1.59", "Not adjusted for splits/dividends (cannot be verified)."],
    ["Daily price change", "Close minus previous close, same symbol", "close(t) - close(t-1)", "Symbol-day", "Prices[daily_change]", "-", "Blank on a symbol's first day."],
    ["Daily percentage return", "% change in close vs previous trading observation of the same symbol", "(close(t)/close(t-1) - 1) x 100", "Symbol-day", "Prices[daily_return_pct]; clean version excludes 13 flagged non-market days", "-", "Sorted by symbol then date before calculating."],
    ["Average daily return", "Mean of clean daily % returns", "AVERAGE(daily_return_clean_pct)", "Selection", "Avg Daily Return %", "-", "Flagged non-market days excluded."],
    ["Period (total) return", "Change in close from first to last record", "(last close / first close - 1) x 100", "Symbol", "Period Return %; Symbols[raw_period_return_pct]", "NVDA +1,120%", "Raw price return; no dividends. Rankings use full-period symbols only."],
    ["Event-adjusted return", "Compounded daily returns with 13 flagged non-market days set to 0%", "prod(1 + r_clean) - 1", "Symbol", "Prices[cum_return_pct]; Symbols[adj_period_return_pct]", "-", "Approximation for spin-offs/splits; verify with vendor adjusted close."],
    ["Daily volatility", "Sample standard deviation of clean daily % returns", "STDEV.S(daily_return_clean_pct)", "Symbol / selection", "Daily Volatility %", "-", "Historical measure; not a forecast."],
    ["Annualised volatility", "Daily volatility scaled to a year", "daily vol x sqrt(252)", "Symbol / selection", "Annualised Volatility %", "CHK 72%, PEP 13%", "Assumes 252 trading days."],
    ["Rolling 20-day volatility", "Std-dev of the last 20 clean daily returns", "rolling(20).std()", "Symbol-day", "Prices[rolling_vol_20]", "-", "Needs 20 observations; past data only."],
    ["Return per unit of risk", "Mean daily return / daily volatility x sqrt(252)", "mean/std x sqrt(252)", "Symbol", "(Python: task4_comparative_stock_table)", "NVDA 1.85", "Simple Sharpe-style ratio, no risk-free rate."],
    ["Daily trading range", "High minus low", "high - low", "Symbol-day", "Prices[daily_range]; Avg Daily Range", "-", "Blank where high/low missing or inconsistent."],
    ["Moving averages (5, 20, 50)", "Mean of the last N closes, same symbol", "rolling(N).mean()", "Symbol-day", "Prices[ma_5/ma_20/ma_50]; Avg MA 5/20/50", "-", "Needs a full window; no look-ahead."],
    ["Average trading volume", "Mean shares traded per day (zero-volume rows excluded)", "AVERAGE(volume | volume > 0)", "Symbol / selection", "Avg Volume", "BAC 89M", "Shares traded - not money value, not revenue."],
    ["Highest / lowest volume", "Max / min non-zero volume", "MAX(volume), MIN(volume | >0)", "Observation", "Max Volume / Min Volume (non-zero)", "VZ 618M on 2014-02-24", ""],
    ["Volume vs price movement", "Spearman correlation between volume and |daily return|", "spearman(volume, abs return)", "Symbol", "Scatter on page 4; Python table", "0.41-0.51 (selected)", "Association only; not causation."],
    ["Full-period history", "Symbol starts within first 10 days of 2014 and trades on 2017-12-29", "rule", "Symbol", "Symbols[history_status]", "483 symbols", "Rankings of returns/volatility use only these."],
    ["Non-market event flag", "Day on the analyst-judgement list of probable spin-offs/splits/data glitch", "list in sp500_utils.NON_MARKET_EVENTS", "Symbol-day", "Prices[extreme_move_flag]", "13 days", "Attributed from general knowledge; verify with vendor."],
]
ws = wb.active; ws.title = "KPI Definitions"
sheet(ws, ["KPI", "Definition", "Formula / method", "Grain", "Power BI field / measure", "Example value", "Notes and limitations"], kpis, [26, 42, 34, 14, 40, 22, 48])
fields = [["symbol", "text", "Stock ticker"], ["date", "date", "Trading date (source text M/D/YYYY converted to date)"], ["open/high/low/close", "number", "Opening / highest / lowest / closing price of the day"],
          ["volume", "integer", "Shares traded that day"], ["year, quarter, month, month_name, year_month, year_quarter", "derived", "Calendar fields from date"],
          ["daily_change", "derived", "close - previous close (same symbol)"], ["daily_return_pct", "derived", "Raw daily % return"], ["daily_return_clean_pct", "derived", "Daily % return with 13 non-market days blanked"],
          ["abs_return_pct", "derived", "Absolute clean daily return"], ["return_bin", "derived", "Clean return clipped to +/-5 and rounded to 0.5 (histogram bucket)"],
          ["daily_range / daily_range_pct", "derived", "high - low; as % of close"], ["ma_5, ma_20, ma_50", "derived", "Moving averages of close"], ["rolling_vol_20", "derived", "20-day rolling std-dev of clean returns"],
          ["cum_return_pct", "derived", "Event-adjusted cumulative return since symbol's first record"],
          ["missing_ohl, zero_volume, ohlc_inconsistent, extreme_move, large_move", "flags", "Data-quality flags (clean dataset only)"]]
sheet(wb.create_sheet("Field Dictionary"), ["Field", "Type", "Meaning"], fields, [52, 12, 80])
sheet(wb.create_sheet("Selected Stocks"), ["Symbol", "Total return %", "Annualised vol %", "Return per unit risk", "Avg volume"],
      [[r.symbol, round(r.total_return_pct, 1), round(r.annualised_volatility_pct, 1), round(r.return_per_unit_risk, 2), round(r.avg_volume)] for r in comp.itertuples()], [12, 16, 18, 20, 16])
wb.save(DOCS / "KPI_Definition_Sheet.xlsx")


# ============================================================================ docx helpers
def new_doc(title, subtitle):
    d = Document()
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)
    for s in d.sections:
        s.left_margin = s.right_margin = Inches(0.9); s.top_margin = s.bottom_margin = Inches(0.8)
    p = d.add_paragraph(); r = p.add_run(title); r.bold = True; r.font.size = Pt(22); r.font.color.rgb = RGBColor.from_string(NAVY)
    p = d.add_paragraph(); r = p.add_run(subtitle); r.font.size = Pt(10); r.font.color.rgb = RGBColor(0x5C, 0x6B, 0x7A)
    return d


def h(d, t, lvl=1):
    p = d.add_heading(t, lvl)
    for r in p.runs: r.font.color.rgb = RGBColor.from_string(NAVY)


def table(d, headers, rows, widths=None):
    t = d.add_table(rows=1, cols=len(headers)); t.style = "Light Grid Accent 1"
    for i, x in enumerate(headers):
        t.rows[0].cells[i].text = ""; run = t.rows[0].cells[i].paragraphs[0].add_run(str(x)); run.bold = True; run.font.size = Pt(9.5)
    for r in rows:
        cells = t.add_row().cells
        for i, x in enumerate(r):
            cells[i].text = ""; run = cells[i].paragraphs[0].add_run(str(x)); run.font.size = Pt(9.5)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Inches(w)
    d.add_paragraph()


def bullets(d, items):
    for x in items: d.add_paragraph(x, style="List Bullet")


# ============================================================================ Data-quality assessment
d = new_doc("Data-Quality Assessment", "S&P 500 Stock Prices 2014-2017 | AnalystLab Africa Week 6 | Track A - Data Analytics")
h(d, "1. Summary")
d.add_paragraph(f"The supplied file contains {dq['records']:,} daily records for {dq['unique_symbols']} symbols over {dq['distinct_dates']:,} trading dates "
                f"({dq['date_min']} to {dq['date_max']}). All data-quality observations listed in the assignment were independently re-validated by script "
                "(02_Scripts/01_inspect_data.py) and confirmed. Additional issues were found and are documented below with the treatment applied.")
h(d, "2. Checks and results")
table(d, ["Check", "Assignment observation", "Validated result", "Treatment"], [
    ["Missing open", "11", dq["missing_values"]["open"], "Left blank (never zero-filled, not imputed)"],
    ["Missing high", "8", dq["missing_values"]["high"], "Left blank"],
    ["Missing low", "8", dq["missing_values"]["low"], "Left blank; daily range blank for these rows"],
    ["Missing close / volume / symbol / date", "-", "0 / 0 / 0 / 0", "None needed"],
    ["Duplicate symbol-date pairs", "None", dq["duplicate_symbol_date"], "None needed"],
    ["Zero-volume rows", "4", dq["zero_volume_rows"], "DHR, O (12 Jan 2016), UA (7 Apr 2016), FTV (1 Jul 2016): valid close but blank O/H/L. Kept in price stats, excluded from volume stats"],
    ["Incomplete stock histories", "Present", f"{dq['symbols_with_incomplete_history']} symbols (22 start late/end early)", "Rankings use 483 full-period symbols; partial ones reported separately"],
    ["Date type", "-", "Text in M/D/YYYY", "Converted to datetime"],
    ["File order", "Check", "Not sorted by symbol/date", "Sorted by symbol then date before every calculation"],
    ["OHLC logically inconsistent rows", "-", dq["ohlc_inconsistent_rows"], "Flagged; daily range blanked (e.g. AOS 19 May 2014 high < low)"],
    ["Daily moves above 25%", "-", f"{dq['moves_over_25pct_total']} total", f"{dq['non_market_events_excluded']} judged probable non-market events (excluded from return/vol stats); {dq['large_moves_retained_flagged']} retained as genuine"],
], [1.7, 1.1, 1.6, 2.6])
h(d, "3. Probable non-market events (excluded from return and volatility statistics)")
d.add_paragraph("The file has no adjusted-close field. The causes below are attributed from general market knowledge, are not stated in the dataset, and should be verified against a corporate-action calendar.")
ev = large[large.treatment.str.startswith("EXCLUDED")]
table(d, ["Symbol", "Date", "Return %", "Prev close", "Close", "Probable cause"],
      [[r.symbol, r.date, f"{r.daily_return_pct:.1f}", f"{r.prev_close:.2f}", f"{r.close:.2f}", r.note] for r in ev.itertuples()], [0.8, 1.0, 0.8, 0.9, 0.8, 2.7])
h(d, "4. Incomplete histories (22 late-start / early-end symbols)")
inc2 = inc.copy(); inc2["first_date"] = pd.to_datetime(inc2.first_date).dt.date; inc2["last_date"] = pd.to_datetime(inc2.last_date).dt.date
table(d, ["Symbol", "First date", "Last date", "Records", "Missing days"], [[r.symbol, r.first_date, r.last_date, r.trading_days, r.missing_days] for r in inc2.itertuples()], [1, 1.3, 1.3, 1, 1.2])
h(d, "5. Limitations that affect interpretation")
bullets(d, [
    "Historical data (2014-2017) - not current market performance.",
    "No adjusted close: splits, dividends and spin-offs cannot be fully verified; AAPL's 2014 7-for-1 split looks pre-adjusted while DISCA/DISCK's 2014 split is not, so adjustment is inconsistent.",
    "Currency is not stated; USD is assumed because the symbols are US-listed (assumption).",
    "Not every symbol was an S&P 500 member for the whole period.",
    "Volume is shares traded, not money value. Returns are price returns (no dividends).",
    "Two of the 13 flagged days belong to a likely data glitch (LNT, 19-20 May 2016: close halves then doubles).",
])
h(d, "6. Validation")
d.add_paragraph(f"{(val.result == 'PASS').sum()} of {len(val)} independent checks passed (08_Validation/Validation_Evidence.md).")
d.save(DOCS / "Data_Quality_Assessment.docx")

# ============================================================================ Executive summary
d = new_doc("Executive Summary - S&P 500 Market Performance Analysis", "AnalystLab Africa | Week 6 | Track A - Data Analytics | Historical data 2 Jan 2014 - 29 Dec 2017")
h(d, "Purpose and scope")
d.add_paragraph("This analysis answers how 505 US stocks behaved between 2014 and 2017: returns, volatility, price movement and trading volume. "
                "It delivers two interactive dashboards (Power BI and Plotly), a reproducible Jupyter notebook and Python pipeline, and independent validation. "
                "All results are historical; none are forecasts or investment advice.")
h(d, "Key findings")
for t in [
    "Leaders and laggards were sector-driven. NVDA (+1,120%), AVGO (+388%) and EA (+360%) led among 483 full-history stocks; energy names led the losers (CHK -85%, RRC -79%). The median stock gained about 49% and 81% finished higher.",
    "Price level is not performance. PCLN's $2,049 peak and CHK's $1.59 low reflect share-price levels; PCLN returned +52% while NVDA, priced under $200, returned +1,120%.",
    "Risk differed five-fold. Annualised volatility ranged from ~13% (PEP, PG, KO) to 59-72% (FCX, AMD, CHK); among selected stocks NFLX (42%) and NVDA (38%) were about three times as volatile as JNJ (14%).",
    "NVDA was the best risk-adjusted performer (1.85 return per unit of risk) versus 1.06-1.07 for MSFT and AMZN; XOM was the only selected stock to lose value (-16%).",
    "Volume rises with the size of price moves: Spearman 0.41-0.51 between volume and absolute daily return for all ten selected stocks.",
    "Selected stocks' daily returns correlate moderately (0.10-0.57), so diversification benefits are visible (WMT/NVDA 0.10; GOOGL/AMZN 0.57 highest).",
    "Data quality changes the answer. 13 non-market days (spin-offs, a split, one data glitch) and 22 partial histories had to be handled before rankings were meaningful.",
]:
    d.add_paragraph(t, style="List Number")
h(d, "Selected-stock comparison")
table(d, ["Stock", "Total return %", "Annualised vol %", "Return per unit risk", "Avg daily volume (M sh.)"],
      [[r.symbol, f"{r.total_return_pct:,.0f}", f"{r.annualised_volatility_pct:.1f}", f"{r.return_per_unit_risk:.2f}", f"{r.avg_volume / 1e6:.1f}"] for r in comp.itertuples()], [1, 1.3, 1.4, 1.5, 1.7])
h(d, "Recommendations")
table(d, ["#", "Recommendation", "Evidence", "How stakeholders can use it"], [
    ["1", "Obtain an adjusted-close / corporate-action feed (or verify the flagged events) before publishing long-term returns.", "13 flagged one-day drops of -35% to -63%; 26 incomplete histories; inconsistent split adjustment.", "Research leads approve return tables only after corporate actions are confirmed."],
    ["2", "Compare stocks using % return, volatility and return per unit of risk together - never raw price.", "PCLN/CHK price extremes vs NVDA/CHK return extremes; NVDA 1.85 vs XOM -0.16 return per risk.", "Analysts shortlist on risk-adjusted performance and scale positions by volatility."],
    ["3", "Use volume spikes as a screening flag for unusual price moves, and pair low-correlation stocks for diversification studies.", "Spearman 0.41-0.51 volume vs move size; correlations 0.10-0.57.", "Monitoring desk flags heavy-volume large-move days; portfolio researchers test pairs such as WMT/NVDA."],
], [0.3, 2.3, 2.2, 2.2])
h(d, "Limitations")
bullets(d, ["Historical (2014-2017) data only; not current. Historical performance does not guarantee future returns.",
            "Prices are not verified as adjusted; currency assumed USD; price returns exclude dividends.",
            "Seasonality patterns come from only four years and are not statistically reliable.",
            "The Power BI project and Plotly page were generated programmatically and must be opened and checked on your machine (see README)."])
h(d, "Deliverables")
d.add_paragraph("Notebook; Python scripts; Power BI project (PBIP); Plotly dashboard (HTML); 13 PNG visualisations; KPI definition sheet; data-quality assessment; validation evidence; this summary; README.")
d.save(DOCS / "Executive_Summary.docx")

# ============================================================================ Power BI guide
guide = f"""# Power BI - Setup and Manual Build Guide

## What is in this folder
| Item | Purpose |
|---|---|
| `SP500_Dashboard.pbip` | Power BI Project - **double-click / open in Power BI Desktop** |
| `SP500_Dashboard.SemanticModel/` | Data model (TMDL): tables Prices, Symbols, Calendar, 2 relationships, 33 DAX measures |
| `SP500_Dashboard.Report/` | Report (PBIR): 4 pages, 46 visuals (slicers, cards, charts, tables) |
| `data/Prices.csv`, `Symbols.csv`, `Calendar.csv` | The data the model loads (497,472 price rows) |
| `Measures.dax`, `PowerQuery_M.txt` | The same DAX and Power Query code as plain text - for the manual route |

## Open the project (5 steps)
1. Use a recent **Power BI Desktop** (2025 or later). If it asks, enable *File > Options > Preview features > Power BI Project (.pbip) save option* and the **TMDL / PBIR** formats, then restart.
2. Copy this whole project folder to a normal local path (e.g. `C:\\Projects\\...`; avoid OneDrive-synced or network paths).
3. Open `SP500_Dashboard.pbip`.
4. **Set the data path once:** Home > Transform data > Edit parameters > `DataFolder` = the full path of the `04_PowerBI\\data` folder (no trailing backslash), e.g. `C:\\Projects\\Week 6 - YOUR NAME - Data Analytics\\04_PowerBI\\data`. Click OK, then **Refresh**.
5. Check the model view shows `Prices (many) -> Symbols (one)` on `symbol` and `Prices (many) -> Calendar (one)` on `date`.

> **Honest status:** this PBIP was generated by script and has not been opened in Power BI Desktop in the build environment. If Desktop reports an error opening it, use the manual route below - it takes about 20 minutes and uses the same data and code.

## How the dashboard behaves
* **Selected-stock default.** Symbol charts show the 10 pre-selected stocks (AAPL, MSFT, AMZN, GOOGL, JPM, XOM, JNJ, NFLX, NVDA, WMT) until you pick symbols in the *Stock symbol* slicer (measure `In Focus`).
* Date range slicer (Calendar[Date], *Between*) filters every visual. Slicers are per page.
* Moving-average chart (page 2): choose **one** symbol, otherwise it averages whatever is selected.
* Returns/volatility use the *clean* daily return (13 flagged non-market days excluded).

## Pages
1. **Market Overview** - total symbols (505), total records, date range, average close, symbols by history completeness, records per year, coverage distribution, closing price by stock, coverage table.
2. **Stock Price Performance** - closing trend, open/high/low/close monthly averages, moving averages 5/20/50, daily range, highest/lowest close.
3. **Returns and Volatility** - daily returns, average daily return, return distribution, annualised and rolling volatility, risk-vs-return scatter.
4. **Trading Volume Analysis** - volume trend, average volume by stock, volume vs price-movement scatter, highest-volume observations, average/highest/lowest volume.

## Manual build route (if the PBIP will not open)
1. Power BI Desktop > *Get data > Text/CSV*: load `Prices.csv`, `Symbols.csv`, `Calendar.csv` (or paste the M code from `PowerQuery_M.txt` into blank queries with a `DataFolder` parameter).
2. Model view: relate `Prices[symbol]` -> `Symbols[symbol]` and `Prices[date]` -> `Calendar[Date]` (many-to-one, single direction).
3. Select the `Prices` table > *New measure*: paste each measure from `Measures.dax`.
4. Build visuals as listed under *Pages* (slicers: Calendar[Date] Between, Symbols[symbol] Dropdown; charts use the `Focus ...` measures so the default is the selected 10 stocks).
5. Save as `SP500_Dashboard.pbix`.

## Verify (do this and take screenshots)
Select AAPL, MSFT, JPM and date range 1 Jan - 31 Dec 2016: **Total Records = 756** and **Avg Close = 75.16** (see `08_Validation/Validation_Evidence.md`, checks V7a/V7b). Save screenshots of the four pages in `10_Screenshots/`.
"""
(u.PBI_DATA.parent / "PowerBI_Setup_and_Manual_Build_Guide.md").write_text(guide, encoding="utf-8")

# ============================================================================ screenshots checklist
(u.ROOT / "10_Screenshots" / "README_screenshots_to_capture.md").write_text("""# Dashboard screenshots - to capture on your machine

The dashboards could not be rendered in the build environment (no Power BI Desktop / no internet for Plotly.js), so real screenshots could not be produced here.
Please capture and save the following (PNG) in this folder:

| File name | What to show |
|---|---|
| powerbi_page1_market_overview.png | Power BI page 1 |
| powerbi_page2_price_performance.png | Page 2 with one symbol selected (moving averages) |
| powerbi_page3_returns_volatility.png | Page 3 |
| powerbi_page4_volume.png | Page 4 |
| powerbi_validation_AAPL_MSFT_JPM_2016.png | Slicers: AAPL, MSFT, JPM and 2016 -> Records 756, Avg Close 75.16 |
| plotly_page1..4.png | The four tabs of 05_Plotly_Dashboard/SP500_Interactive_Dashboard.html |
""", encoding="utf-8")

# ============================================================================ requirements + README
(u.ROOT / "02_Scripts" / "requirements.txt").write_text("pandas>=2.0\nnumpy\nscipy\nmatplotlib\nseaborn\npython-docx\nopenpyxl\nplotly  # only needed to run the optional Plotly cell in the notebook\njupyter  # to re-run the notebook\n")
readme = f"""# S&P 500 Stock Market Performance and Business Intelligence Dashboard
**AnalystLab Africa - Experience Lab Internship - Week 6 - Track A: Data Analytics**

> Rename this folder to `Week 6 - <Your Full Name> - Data Analytics` before submitting.

## Purpose
Analyse 505 US stocks over 2 Jan 2014 - 29 Dec 2017 (497,472 daily records): returns, volatility, price movement and trading volume, and present them in interactive dashboards.
All findings are **historical**, not current market data and not investment advice.

## Folder guide
| Folder | Contents |
|---|---|
| `01_Data/raw` | Original CSV (untouched) |
| `01_Data/processed` | `sp500_clean_full.csv` (clean + engineered fields), `sp500_selected_stocks.csv`, `symbol_summary.csv` |
| `02_Scripts` | Reproducible pipeline `01`-`09` + `sp500_utils.py` + `requirements.txt` |
| `03_Notebook` | `SP500_Track_A_Data_Analytics.ipynb` (executed, outputs included) |
| `04_PowerBI` | **Power BI project** `SP500_Dashboard.pbip`, data CSVs, DAX, M code, setup guide |
| `05_Plotly_Dashboard` | `SP500_Interactive_Dashboard.html` (Plotly, 4 pages, filters) |
| `06_Visualisations` | 13 analytical PNG charts |
| `07_Analysis_Outputs` | Result tables for every question + data-quality detail tables |
| `08_Validation` | `Validation_Evidence.md`, `validation_results.csv` (41 independent checks) |
| `09_Documentation` | KPI definition sheet, data-quality assessment, executive summary |
| `10_Screenshots` | Checklist - screenshots must be captured on your machine |

## How to reproduce
```
cd 02_Scripts
pip install -r requirements.txt
python 01_inspect_data.py       # data-quality checks
python 02_prepare_data.py       # clean + features + Power BI tables
python 03_analysis.py           # 8 questions + comparative analysis
python 04_make_visuals.py       # PNG charts
python 05_validate.py           # independent validation
python 06_build_plotly_dashboard.py
python 07_build_powerbi_project.py
python 08_build_notebook.py     # executes and saves the notebook
python 09_build_docs.py
```
(Scripts import `sp500_utils`; run them from inside `02_Scripts`.)

## Method in brief
* Sort by symbol then date; all calculations are per symbol. Date text (M/D/YYYY) converted to dates.
* Fields: year, month, quarter, daily change, daily % return, daily range (high-low), moving averages 5/20/50, rolling 20-day volatility.
* Missing open/high/low are left blank (never zero). Zero-volume rows stay but are excluded from volume statistics.
* The file has **no adjusted close**. 13 days judged probable spin-offs/splits/data glitch are excluded from return and volatility statistics (list in `sp500_utils.NON_MARKET_EVENTS`; the causes come from general knowledge and must be verified).
* Rankings of returns/volatility use the 483 symbols with a full-period history. Ten selected stocks (AAPL, MSFT, AMZN, GOOGL, JPM, XOM, JNJ, NFLX, NVDA, WMT) are compared in detail.

## Headline results (historical)
* Best return among full-history stocks: NVDA +1,120%; worst CHK -85%. Median +49%.
* Most volatile: CHK 72% annualised; least: PEP ~13%.
* Highest average volume: BAC (~89M shares/day). Volume and |daily return| correlate 0.41-0.51 for the selected stocks.
* Full detail: `09_Documentation/Executive_Summary.docx`.

## Assumptions and limitations
* Currency not in the file; USD assumed. Prices not verified as split/dividend-adjusted; returns exclude dividends.
* Not every symbol was in the S&P 500 throughout the period; 22 symbols have partial histories.
* Plotly dashboard needs internet (loads Plotly.js from the Plotly CDN) and embeds 60 stocks (10 selected + 50 most-traded); Power BI covers all 505.
* **The Power BI project and Plotly page were generated programmatically and could not be opened in Power BI Desktop or a browser in the build environment.** Open them, follow `04_PowerBI/PowerBI_Setup_and_Manual_Build_Guide.md`, run the check described there, and add screenshots to `10_Screenshots`. The JavaScript passed a syntax check and a simulated render test; the PBIP JSON parses, but Desktop compatibility is untested.
* Python tools used: pandas, NumPy, SciPy, Matplotlib, Seaborn (Plotly.js for the dashboard). Notebook executed with a lightweight runner, not Jupyter.

## Professional-development checklist
GitHub repo update; LinkedIn post (tag AnalystLab Africa, #AnalystLabAfrica); X post (@analystlabafric, #AnalystLabAfrica); 5-10 minute recorded presentation.
"""
(u.ROOT / "README.md").write_text(readme, encoding="utf-8")
print("docs written:", sorted(p.name for p in DOCS.iterdir()))
