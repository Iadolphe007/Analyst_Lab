# Week 6 — S&P 500 Data Analytics

## Overview
Track A analysis of historical S&P 500 constituent-symbol price records (2014–2017), using Python/Pandas and Plotly.

## Files
- `S&P500_Data_Analytics.ipynb`: reproducible notebook
- `data_preparation.py`: reusable preparation function/script
- `cleaned_stock_data.csv`: prepared dataset with features
- `interactive_dashboard.html`: interactive Plotly visualizations
- `visualizations/`: HTML charts and PNG evidence
- `KPI_definition_sheet.xlsx`: KPI definitions
- `data_quality_assessment.xlsx`: data-quality findings
- `validation_evidence.xlsx`: independent calculation checks
- `selected_stock_kpis.xlsx`: selected-stock metrics
- `Executive_Summary.pdf`: findings and recommendations

## Run
1. Put the original CSV beside the notebook (or change DATA_PATH).
2. Install packages: `pip install pandas numpy matplotlib plotly jupyter openpyxl`
3. Run `python data_preparation.py` to create the cleaned dataset.
4. Open and run `S&P500_Data_Analytics.ipynb`.
5. Open `interactive_dashboard.html` in a browser.

## Dashboard
The HTML dashboard contains interactive Plotly charts (hover, zoom, pan, legend toggling). This generated HTML is a static multi-chart dashboard rather than a server-based dashboard with global cross-chart filters. The notebook charts and prepared CSV allow further symbol/date filtering.

## Data preparation decisions
- Parsed date and sorted by symbol/date.
- Filled missing opening prices with that observation's close.
- Filled missing high/low using the row-level maximum/minimum among remaining observed OHLC prices.
- Derived year, month, quarter, daily price change, daily return %, trading range, MA5/MA20/MA50.
- Calculations are grouped by symbol to avoid cross-symbol leakage.

## Data overview
- 497,472 rows; 505 symbols; 1,007 distinct dates
- Period: 2014-01-02 to 2017-12-29
- Duplicate symbol-date pairs: 0
- Missing original values: open=11, high=8, low=8
- Zero volume observations: 4

## Limitations
Historical data only; not current performance or investment advice. No adjusted close field: dividends/splits may affect period comparisons. Incomplete histories. Currency is not specified. Imputed records and period return from first-to-last available prices require caution.

## Method
Period return=(last available close / first available close - 1)*100. Annualized historical volatility=std daily return percentage * sqrt(252). This is an approximation and is not a forecast.
\n## Optional filterable dashboard app\nThe Streamlit dashboard source is `dashboard_app.py`. Install `streamlit` then run `streamlit run dashboard_app.py` from this folder. It provides symbol and date-range filters.\n