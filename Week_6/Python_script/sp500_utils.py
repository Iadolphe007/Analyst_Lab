"""
sp500_utils.py - shared helpers for the S&P 500 Track A (Data Analytics) project.

All scripts import from here so that definitions (returns, moving averages,
extreme-move rule, selected stocks) are identical everywhere.
"""
from pathlib import Path
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Paths (relative to the project root, so the project can be moved anywhere)
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "01_Data" / "raw" / "SP 500 Stock Prices 2014-2017.csv"
PROCESSED = ROOT / "01_Data" / "processed"
PBI_DATA = ROOT / "04_PowerBI" / "data"
OUT = ROOT / "07_Analysis_Outputs"
VIS = ROOT / "06_Visualisations"
VAL = ROOT / "08_Validation"
DOCS = ROOT / "09_Documentation"

# --------------------------------------------------------------------------
# Project-wide analytical definitions
# --------------------------------------------------------------------------
# Ten large, liquid, full-history stocks from different sectors.
SELECTED = ["AAPL", "MSFT", "AMZN", "GOOGL", "JPM", "XOM", "JNJ", "NFLX", "NVDA", "WMT"]

# The file has no adjusted-close field, so a few one-day price drops are almost
# certainly spin-offs / splits / special dividends (not market returns), and one
# pair is a data glitch. They are listed here, found by screening every daily
# move above LARGE_MOVE_PCT and then judging each case. The cause is attributed
# from general market knowledge - it is NOT stated in the dataset and should be
# verified against the data vendor's corporate-action calendar.
# These days are excluded from volatility / average-return statistics and
# contribute 0% to the event-adjusted cumulative return.
LARGE_MOVE_PCT = 25.0
NON_MARKET_EVENTS = {
    ("NI", "2015-07-02"): "Probable spin-off (Columbia Pipeline Group)",
    ("EBAY", "2015-07-20"): "Probable spin-off (PayPal)",
    ("DISCA", "2014-08-07"): "Probable 2-for-1 split (stock dividend)",
    ("DISCK", "2014-08-07"): "Probable 2-for-1 split (stock dividend)",
    ("BAX", "2015-07-01"): "Probable spin-off (Baxalta)",
    ("A", "2014-11-03"): "Probable spin-off (Keysight Technologies)",
    ("ARNC", "2016-11-01"): "Probable separation (Alcoa Corp / Arconic)",
    ("YUM", "2016-11-01"): "Probable spin-off (Yum China)",
    ("CAG", "2016-11-10"): "Probable spin-off (Lamb Weston)",
    ("HPE", "2017-04-03"): "Probable spin-off/merger (Enterprise Services -> DXC)",
    ("BHGE", "2017-07-05"): "Probable special dividend after GE/Baker Hughes deal",
    ("LNT", "2016-05-19"): "Data glitch: close halves then returns next day",
    ("LNT", "2016-05-20"): "Data glitch: reversal of the previous day",
}

TRADING_DAYS_PER_YEAR = 252
MA_WINDOWS = (5, 20, 50)
ROLL_VOL_WINDOW = 20


def load_raw() -> pd.DataFrame:
    """Load the original CSV untouched except for date parsing (M/D/YYYY)."""
    df = pd.read_csv(RAW_CSV, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    return df


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Sort, flag data-quality problems and engineer analytical fields.

    Every per-symbol calculation uses groupby('symbol') on data that is sorted
    by symbol then date, so nothing leaks across stocks.
    """
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True).copy()
    g = df.groupby("symbol", sort=False)

    # ---- calendar fields -------------------------------------------------
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["year_quarter"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)

    # ---- data-quality flags ---------------------------------------------
    df["missing_ohl"] = df[["open", "high", "low"]].isna().any(axis=1)
    df["zero_volume"] = df["volume"] == 0
    hl = df[["high", "low"]].notna().all(axis=1)
    tol = 1e-9
    df["ohlc_inconsistent"] = hl & (
        (df["high"] < df["low"] - tol)
        | (df["close"] > df["high"] + tol)
        | (df["close"] < df["low"] - tol)
    )

    # ---- price change & returns -----------------------------------------
    df["daily_change"] = g["close"].diff()
    df["daily_return_pct"] = g["close"].pct_change(fill_method=None) * 100
    keys = list(zip(df["symbol"], df["date"].dt.strftime("%Y-%m-%d")))
    df["extreme_move"] = [k in NON_MARKET_EVENTS for k in keys]          # excluded from stats
    df["large_move"] = (df["daily_return_pct"].abs() > LARGE_MOVE_PCT) & ~df["extreme_move"]  # kept, flagged
    df["daily_return_clean_pct"] = df["daily_return_pct"].where(~df["extreme_move"])
    df["abs_return_pct"] = df["daily_return_clean_pct"].abs()

    # event-adjusted cumulative return (flagged days contribute 0%)
    step = (df["daily_return_clean_pct"].fillna(0) / 100) + 1
    df["cum_return_pct"] = (step.groupby(df["symbol"], sort=False).cumprod() - 1) * 100
    df["return_bin"] = (df["daily_return_clean_pct"].clip(-5, 5) * 2).round() / 2

    # ---- range (only where high/low are valid) --------------------------
    valid_range = hl & ~df["ohlc_inconsistent"]
    df["daily_range"] = (df["high"] - df["low"]).where(valid_range)
    df["daily_range_pct"] = (df["daily_range"] / df["close"] * 100)

    # ---- moving averages & rolling volatility (past data only) ----------
    for w in MA_WINDOWS:
        df[f"ma_{w}"] = g["close"].transform(lambda s, w=w: s.rolling(w, min_periods=w).mean())
    df["rolling_vol_20"] = (
        df.groupby("symbol", sort=False)["daily_return_clean_pct"]
        .transform(lambda s: s.rolling(ROLL_VOL_WINDOW, min_periods=ROLL_VOL_WINDOW).std())
    )
    return df


def symbol_summary(df: pd.DataFrame, n_dates: int | None = None) -> pd.DataFrame:
    """One row per symbol with coverage, price, return, volatility, volume KPIs."""
    n_dates = n_dates or df["date"].nunique()
    first_date, last_date = df["date"].min(), df["date"].max()
    rows = []
    for sym, d in df.groupby("symbol", sort=True):
        d = d.sort_values("date")
        vol_ok = d.loc[d["volume"] > 0, "volume"]
        r = d["daily_return_clean_pct"].dropna()
        full_period = (d["date"].min() <= first_date + pd.Timedelta(days=10)) and d["date"].max() == last_date
        rows.append(dict(
            symbol=sym,
            first_date=d["date"].min().date(),
            last_date=d["date"].max().date(),
            trading_days=len(d),
            coverage_pct=round(len(d) / n_dates * 100, 2),
            history_status="Full period" if full_period else "Partial history",
            first_close=d["close"].iloc[0],
            last_close=d["close"].iloc[-1],
            avg_close=d["close"].mean(),
            max_close=d["close"].max(),
            max_close_date=d.loc[d["close"].idxmax(), "date"].date(),
            min_close=d["close"].min(),
            min_close_date=d.loc[d["close"].idxmin(), "date"].date(),
            raw_period_return_pct=(d["close"].iloc[-1] / d["close"].iloc[0] - 1) * 100,
            adj_period_return_pct=d["cum_return_pct"].iloc[-1],
            avg_daily_return_pct=r.mean(),
            daily_volatility_pct=r.std(),
            annualised_volatility_pct=r.std() * np.sqrt(TRADING_DAYS_PER_YEAR),
            avg_volume=vol_ok.mean(),
            max_volume=d["volume"].max(),
            extreme_move_days=int(d["extreme_move"].sum()),
            is_selected="Yes" if sym in SELECTED else "No",
        ))
    out = pd.DataFrame(rows)
    return out
