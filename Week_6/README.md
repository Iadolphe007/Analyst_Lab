# S&P 500 Stock Market Performance and Business Intelligence Dashboard
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
