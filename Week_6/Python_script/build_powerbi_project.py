"""
07_build_powerbi_project.py - generates the Power BI Project (PBIP) in 04_PowerBI/.

PBIP = Microsoft's text-based Power BI format (open SP500_Dashboard.pbip in Power BI Desktop):
  SP500_Dashboard.SemanticModel/  TMDL data model (3 tables, 2 relationships, DAX measures, Power Query M)
  SP500_Dashboard.Report/         PBIR report: 4 pages, slicers, cards and charts
  data/                           Prices.csv, Symbols.csv, Calendar.csv produced by 02_prepare_data.py
Also writes Measures.dax and PowerQuery_M.txt so the model can be rebuilt by hand if needed.
"""
import json, hashlib, uuid, shutil
from pathlib import Path
import sp500_utils as u

PBI = u.ROOT / "04_PowerBI"
SM = PBI / "SP500_Dashboard.SemanticModel"
RP = PBI / "SP500_Dashboard.Report"
for p in (SM, RP):
    if p.exists():
        shutil.rmtree(p)
(SM / "definition" / "tables").mkdir(parents=True)
(RP / "definition" / "pages").mkdir(parents=True)
g = lambda: str(uuid.uuid4())
PLACEHOLDER = r"C:\REPLACE\WITH\YOUR\PATH\Week 6 - YOUR NAME - Data Analytics\04_PowerBI\data"

# ======================================================================= semantic model
PRICE_COLS = [("symbol", "string", None), ("date", "dateTime", "yyyy-mm-dd"), ("open", "double", "#,0.00"), ("high", "double", "#,0.00"),
              ("low", "double", "#,0.00"), ("close", "double", "#,0.00"), ("volume", "int64", "#,0"),
              ("daily_change", "double", "#,0.00"), ("daily_return_pct", "double", "0.00"), ("daily_return_clean_pct", "double", "0.00"),
              ("abs_return_pct", "double", "0.00"), ("return_bin", "double", "0.0"), ("daily_range", "double", "#,0.00"),
              ("daily_range_pct", "double", "0.00"), ("ma_5", "double", "#,0.00"), ("ma_20", "double", "#,0.00"), ("ma_50", "double", "#,0.00"),
              ("rolling_vol_20", "double", "0.00"), ("cum_return_pct", "double", "0.00"), ("extreme_move_flag", "int64", "0"),
              ("large_move_flag", "int64", "0"), ("zero_volume_flag", "int64", "0")]
SYM_COLS = [("symbol", "string", None), ("first_date", "dateTime", "yyyy-mm-dd"), ("last_date", "dateTime", "yyyy-mm-dd"),
            ("trading_days", "int64", "#,0"), ("coverage_pct", "double", "0.0"), ("history_status", "string", None),
            ("first_close", "double", "#,0.00"), ("last_close", "double", "#,0.00"), ("avg_close", "double", "#,0.00"),
            ("max_close", "double", "#,0.00"), ("max_close_date", "dateTime", "yyyy-mm-dd"), ("min_close", "double", "#,0.00"),
            ("min_close_date", "dateTime", "yyyy-mm-dd"), ("raw_period_return_pct", "double", "0.0"), ("adj_period_return_pct", "double", "0.0"),
            ("avg_daily_return_pct", "double", "0.000"), ("daily_volatility_pct", "double", "0.00"), ("annualised_volatility_pct", "double", "0.0"),
            ("avg_volume", "double", "#,0"), ("max_volume", "int64", "#,0"), ("extreme_move_days", "int64", "0"), ("is_selected", "string", None),
            ("coverage_bucket", "string", None), ("first_year", "int64", "0")]
CAL_COLS = [("Date", "dateTime", "yyyy-mm-dd"), ("Year", "int64", "0"), ("QuarterNum", "int64", "0"), ("Quarter", "string", None),
            ("YearQuarter", "string", None), ("MonthNum", "int64", "0"), ("MonthName", "string", None), ("YearMonth", "string", None)]

TYPE_M = {"string": "type text", "dateTime": "type date", "double": "type number", "int64": "Int64.Type"}

# Measures: name -> (DAX, format)
FOCUS = ("VAR nAll = COUNTROWS(ALL(Symbols[symbol])) VAR nSel = COUNTROWS(ALLSELECTED(Symbols[symbol])) "
         "RETURN IF(nSel < nAll, TRUE(), SELECTEDVALUE(Symbols[is_selected], \"No\") = \"Yes\")")
M = {
    "Total Symbols": ("DISTINCTCOUNT(Prices[symbol])", "#,0"),
    "Total Records": ("COUNTROWS(Prices)", "#,0"),
    "Start Date": ("MIN(Prices[date])", "yyyy-mm-dd"),
    "End Date": ("MAX(Prices[date])", "yyyy-mm-dd"),
    "Symbol Count": ("DISTINCTCOUNT(Symbols[symbol])", "#,0"),
    "Avg Close": ("AVERAGE(Prices[close])", "#,0.00"),
    "Max Close": ("MAX(Prices[close])", "#,0.00"),
    "Min Close": ("MIN(Prices[close])", "#,0.00"),
    "Avg Open": ("AVERAGE(Prices[open])", "#,0.00"),
    "Avg High": ("AVERAGE(Prices[high])", "#,0.00"),
    "Avg Low": ("AVERAGE(Prices[low])", "#,0.00"),
    "Avg MA 5": ("AVERAGE(Prices[ma_5])", "#,0.00"),
    "Avg MA 20": ("AVERAGE(Prices[ma_20])", "#,0.00"),
    "Avg MA 50": ("AVERAGE(Prices[ma_50])", "#,0.00"),
    "Avg Daily Range": ("AVERAGE(Prices[daily_range])", "#,0.00"),
    "Avg Daily Return %": ("AVERAGE(Prices[daily_return_clean_pct])", "0.000"),
    "Daily Volatility %": ("STDEV.S(Prices[daily_return_clean_pct])", "0.00"),
    "Annualised Volatility %": ("[Daily Volatility %] * SQRT(252)", "0.0"),
    "Avg Rolling Vol 20 (annualised %)": ("AVERAGE(Prices[rolling_vol_20]) * SQRT(252)", "0.0"),
    "Avg Abs Return %": ("AVERAGE(Prices[abs_return_pct])", "0.00"),
    "Avg Cumulative Return %": ("AVERAGE(Prices[cum_return_pct])", "0.0"),
    "Avg Volume": ("CALCULATE(AVERAGE(Prices[volume]), Prices[volume] > 0)", "#,0"),
    "Max Volume": ("MAX(Prices[volume])", "#,0"),
    "Min Volume (non-zero)": ("CALCULATE(MIN(Prices[volume]), Prices[volume] > 0)", "#,0"),
    "Period Return %": ("AVERAGEX(VALUES(Prices[symbol]), VAR d1 = CALCULATE(MIN(Prices[date])) VAR d2 = CALCULATE(MAX(Prices[date])) "
                        "VAR c1 = CALCULATE(MAX(Prices[close]), Prices[date] = d1) VAR c2 = CALCULATE(MAX(Prices[close]), Prices[date] = d2) "
                        "RETURN DIVIDE(c2 - c1, c1) * 100)", "0.0"),
    # "Focus" measures: with no symbol slicer they show the 10 selected stocks; with a slicer they show the chosen symbols.
    "In Focus": (FOCUS, "TRUE/FALSE"),
    "Focus Close": ("IF([In Focus], [Avg Close])", "#,0.00"),
    "Focus Avg Daily Return %": ("IF([In Focus], [Avg Daily Return %])", "0.000"),
    "Focus Annualised Volatility %": ("IF([In Focus], [Annualised Volatility %])", "0.0"),
    "Focus Rolling Vol 20 (annualised %)": ("IF([In Focus], [Avg Rolling Vol 20 (annualised %)])", "0.0"),
    "Focus Cumulative Return %": ("IF([In Focus], [Avg Cumulative Return %])", "0.0"),
    "Focus Avg Volume": ("IF([In Focus], [Avg Volume])", "#,0"),
    "Focus Records": ("IF([In Focus], [Total Records])", "#,0"),
}
MEAS_NOTE = {"In Focus": "Shows the 10 pre-selected stocks until the user picks symbols in the slicer."}


def dax_block(expr):
    return expr


def table_tmdl(name, cols, source_csv, measures=None):
    L = [f"table {name}", f"\tlineageTag: {g()}", ""]
    for n, t, f in cols:
        L += [f"\tcolumn {n}", f"\t\tdataType: {t}", f"\t\tlineageTag: {g()}"]
        if f:
            L.append(f"\t\tformatString: {f}")
        L += ["\t\tsummarizeBy: none", f"\t\tsourceColumn: {n}", ""]
    for mn, (expr, fmt) in (measures or {}).items():
        qn = f"'{mn}'" if (" " in mn or "%" in mn or "(" in mn) else mn
        L += [f"\tmeasure {qn} = {expr}"]
        if fmt not in ("TRUE/FALSE",):
            L.append(f"\t\tformatString: {fmt}")
        L += [f"\t\tlineageTag: {g()}", ""]
    types = ", ".join('{"%s", %s}' % (n, TYPE_M[t]) for n, t, _ in cols)
    L += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
          f'\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & "\\{source_csv}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          "\t\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
          f'\t\t\t\t    Typed = Table.TransformColumnTypes(Headers, {{{types}}}, "en-US")',
          "\t\t\t\tin", "\t\t\t\t    Typed", "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(L)


(SM / "definition.pbism").write_text(json.dumps({"version": "4.0", "settings": {}}, indent=2))
D = SM / "definition"
(D / "database.tmdl").write_text("database SP500_Dashboard\n\tcompatibilityLevel: 1600\n")
(D / "model.tmdl").write_text(
    "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\n"
    'annotation PBI_QueryOrder = ["DataFolder","Prices","Symbols","Calendar"]\n\n'
    "ref table Prices\nref table Symbols\nref table Calendar\nref expression DataFolder\n")
(D / "expressions.tmdl").write_text(
    f'expression DataFolder = "{PLACEHOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
    f"\tlineageTag: {g()}\n\tqueryGroup: Parameters\n\n\tannotation PBI_ResultType = Text\n")
(D / "relationships.tmdl").write_text(
    f"relationship {g()}\n\tfromColumn: Prices.symbol\n\ttoColumn: Symbols.symbol\n\n"
    f"relationship {g()}\n\tfromColumn: Prices.date\n\ttoColumn: Calendar.Date\n")
(D / "tables" / "Prices.tmdl").write_text(table_tmdl("Prices", PRICE_COLS, "Prices.csv", M))
(D / "tables" / "Symbols.tmdl").write_text(table_tmdl("Symbols", SYM_COLS, "Symbols.csv"))
(D / "tables" / "Calendar.tmdl").write_text(table_tmdl("Calendar", CAL_COLS, "Calendar.csv"))

# helper exports --------------------------------------------------------------------------
(PBI / "Measures.dax").write_text(
    "// DAX measures for the SP500_Dashboard model. Create them in the 'Prices' table (Modeling > New measure).\n\n" +
    "\n\n".join(f"{n} =\n    {e}" for n, (e, _) in M.items()), encoding="utf-8")
mtxt = [f'// Power Query (M). 1) New parameter  DataFolder  (Text) = the full path of the 04_PowerBI\\data folder',
        "// 2) Home > New source > Blank query > Advanced editor, paste one block per table, name it Prices / Symbols / Calendar.\n"]
for nm, cols, f in (("Prices", PRICE_COLS, "Prices.csv"), ("Symbols", SYM_COLS, "Symbols.csv"), ("Calendar", CAL_COLS, "Calendar.csv")):
    types = ", ".join('{"%s", %s}' % (n, TYPE_M[t]) for n, t, _ in cols)
    mtxt.append(f'// ---- {nm} ----\nlet\n    Source = Csv.Document(File.Contents(DataFolder & "\\{f}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n'
                f'    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n    Typed = Table.TransformColumnTypes(Headers, {{{types}}}, "en-US")\nin\n    Typed\n')
(PBI / "PowerQuery_M.txt").write_text("\n".join(mtxt), encoding="utf-8")

# ======================================================================= report (PBIR)
(PBI / "SP500_Dashboard.pbip").write_text(json.dumps(
    {"version": "1.0", "artifacts": [{"report": {"path": "SP500_Dashboard.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))
(RP / "definition.pbir").write_text(json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": "../SP500_Dashboard.SemanticModel"}}}, indent=2))
RD = RP / "definition"
SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
(RD / "version.json").write_text(json.dumps({"$schema": SCH + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
(RD / "report.json").write_text(json.dumps({
    "$schema": SCH + "report/1.0.0/schema.json",
    "themeCollection": {"baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55", "type": "SharedResources"}},
    "layoutOptimization": "None"}, indent=2))


def col(ent, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}


def mea(prop, ent="Prices"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": ent}}, "Property": prop}}


def proj(field, active=False):
    k = "Column" if "Column" in field else "Measure"
    ent = field[k]["Expression"]["SourceRef"]["Entity"]; prop = field[k]["Property"]
    p = {"field": field, "queryRef": f"{ent}.{prop}", "nativeQueryRef": prop}
    if active:
        p["active"] = True
    return p


lit = lambda s: {"expr": {"Literal": {"Value": "'" + s.replace("'", "''") + "'"}}}
tru = {"expr": {"Literal": {"Value": "true"}}}


def visual(vid, vtype, x, y, w, h, title=None, query=None, objects=None, sort=None, z=0):
    v = {"visualType": vtype, "drillFilterOtherVisuals": True}
    if query:
        qs = {role: {"projections": [proj(f, a) for f, a in fl]} for role, fl in query.items()}
        v["query"] = {"queryState": qs}
        if sort:
            v["query"]["sortDefinition"] = {"sort": [{"field": sort, "direction": "Descending"}], "isDefaultSort": True}
    if objects:
        v["objects"] = objects
    if title:
        v["visualContainerObjects"] = {"title": [{"properties": {"show": tru, "text": lit(title)}}]}
    return {"$schema": SCH + "visualContainer/1.0.0/schema.json", "name": vid,
            "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": v}


def textbox(vid, x, y, w, h, text, size="20pt", bold=True, color="#14324A"):
    obj = {"general": [{"properties": {"paragraphs": [{"textRuns": [{"value": text, "textStyle": {"fontSize": size, "fontWeight": "bold" if bold else "normal", "color": color}}]}]}}]}
    return {"$schema": SCH + "visualContainer/1.0.0/schema.json", "name": vid,
            "position": {"x": x, "y": y, "z": 0, "height": h, "width": w, "tabOrder": 0}, "visual": {"visualType": "textbox", "objects": obj, "drillFilterOtherVisuals": True}}


def slicer(vid, field, x, y, w, h, mode, title):
    return visual(vid, "slicer", x, y, w, h, title, {"Values": [(field, False)]},
                  {"data": [{"properties": {"mode": lit(mode)}}]})


def card(vid, m, x, y, w, h, title):
    return visual(vid, "card", x, y, w, h, title, {"Values": [(mea(m), False)]})


DATE = col("Calendar", "Date"); SYMS = col("Symbols", "symbol")
pages = []


def header(pid, title, subtitle):
    return [textbox(f"{pid}_t", 20, 8, 900, 40, title), textbox(f"{pid}_s", 20, 44, 1240, 22, subtitle, "10pt", False, "#5C6B7A")]


# ---- Page 1 Market Overview
P = "pg1"
v = header(P, "S&P 500 Market Overview", "Historical daily prices 2014-2017 (not current market data). Symbol charts show the 10 selected stocks until you pick symbols.")
v += [slicer(f"{P}_s1", DATE, 20, 72, 380, 56, "Between", "Date range"), slicer(f"{P}_s2", SYMS, 420, 72, 300, 56, "Dropdown", "Stock symbol")]
for i, (m, t) in enumerate([("Total Symbols", "Total stock symbols"), ("Total Records", "Total trading records"), ("Start Date", "Available from"),
                            ("End Date", "Available to"), ("Avg Close", "Average closing price (current selection)")]):
    v.append(card(f"{P}_c{i}", m, 20 + i * 250, 136, 235, 84, t))
v += [visual(f"{P}_v1", "donutChart", 20, 232, 400, 240, "Symbols by history completeness", {"Category": [(col("Symbols", "history_status"), False)], "Y": [(mea("Symbol Count"), False)]}),
      visual(f"{P}_v2", "clusteredColumnChart", 440, 232, 400, 240, "Trading records per year", {"Category": [(col("Calendar", "Year"), False)], "Y": [(mea("Total Records"), False)]}),
      visual(f"{P}_v3", "clusteredColumnChart", 860, 232, 400, 240, "Symbol distribution by data coverage", {"Category": [(col("Symbols", "coverage_bucket"), False)], "Y": [(mea("Symbol Count"), False)]}),
      visual(f"{P}_v4", "clusteredBarChart", 20, 484, 620, 226, "Average closing price by stock", {"Category": [(SYMS, False)], "Y": [(mea("Focus Close"), False)]}, sort=mea("Focus Close")),
      visual(f"{P}_v5", "tableEx", 660, 484, 600, 226, "Symbol coverage",
             {"Values": [(SYMS, False), (col("Symbols", "first_date"), False), (col("Symbols", "last_date"), False), (col("Symbols", "trading_days"), False), (col("Symbols", "history_status"), False)]})]
pages.append((P, "Market Overview", v))

# ---- Page 2 Stock Price Performance
P = "pg2"
v = header(P, "Stock Price Performance", "Closing prices, open/high/low comparison, daily movements and moving averages. Pick one symbol for the moving-average chart.")
v += [slicer(f"{P}_s1", DATE, 20, 72, 380, 56, "Between", "Date range"), slicer(f"{P}_s2", SYMS, 420, 72, 300, 56, "Dropdown", "Stock symbol"),
      card(f"{P}_c1", "Max Close", 740, 72, 240, 56, "Highest close"), card(f"{P}_c2", "Min Close", 1000, 72, 240, 56, "Lowest close")]
v += [visual(f"{P}_v1", "lineChart", 20, 140, 820, 280, "Closing price trend", {"Category": [(col("Prices", "date"), True)], "Y": [(mea("Focus Close"), False)], "Series": [(SYMS, False)]}),
      visual(f"{P}_v2", "lineChart", 860, 140, 400, 280, "Open, high, low and close (monthly average)",
             {"Category": [(col("Calendar", "YearMonth"), True)], "Y": [(mea("Avg Open"), False), (mea("Avg High"), False), (mea("Avg Low"), False), (mea("Avg Close"), False)]}),
      visual(f"{P}_v3", "lineChart", 20, 432, 620, 278, "Moving averages (5 / 20 / 50 days) - pick one symbol",
             {"Category": [(col("Prices", "date"), True)], "Y": [(mea("Avg Close"), False), (mea("Avg MA 5"), False), (mea("Avg MA 20"), False), (mea("Avg MA 50"), False)]}),
      visual(f"{P}_v4", "clusteredColumnChart", 660, 432, 600, 278, "Daily price movement: average daily range (high - low)",
             {"Category": [(col("Calendar", "YearMonth"), False)], "Y": [(mea("Avg Daily Range"), False)]})]
pages.append((P, "Stock Price Performance", v))

# ---- Page 3 Returns & Volatility
P = "pg3"
v = header(P, "Returns and Volatility", "Daily % returns (13 flagged non-market events excluded). Volatility = standard deviation of daily returns; annualised x sqrt(252).")
v += [slicer(f"{P}_s1", DATE, 20, 72, 380, 56, "Between", "Date range"), slicer(f"{P}_s2", SYMS, 420, 72, 300, 56, "Dropdown", "Stock symbol"),
      card(f"{P}_c1", "Avg Daily Return %", 740, 72, 240, 56, "Average daily return %"), card(f"{P}_c2", "Annualised Volatility %", 1000, 72, 240, 56, "Annualised volatility %")]
v += [visual(f"{P}_v1", "lineChart", 20, 140, 620, 270, "Daily percentage returns", {"Category": [(col("Prices", "date"), True)], "Y": [(mea("Focus Avg Daily Return %"), False)], "Series": [(SYMS, False)]}),
      visual(f"{P}_v2", "clusteredColumnChart", 660, 140, 600, 270, "Return distribution (count of days by return bucket, %)", {"Category": [(col("Prices", "return_bin"), False)], "Y": [(mea("Focus Records"), False)]}),
      visual(f"{P}_v3", "clusteredBarChart", 20, 420, 400, 290, "Historical volatility (annualised %)", {"Category": [(SYMS, False)], "Y": [(mea("Focus Annualised Volatility %"), False)]}, sort=mea("Focus Annualised Volatility %")),
      visual(f"{P}_v4", "lineChart", 440, 420, 420, 290, "Rolling 20-day volatility (annualised %)", {"Category": [(col("Prices", "date"), True)], "Y": [(mea("Focus Rolling Vol 20 (annualised %)"), False)], "Series": [(SYMS, False)]}),
      visual(f"{P}_v5", "scatterChart", 880, 420, 380, 290, "Risk vs average return (all symbols)", {"Category": [(SYMS, False)], "X": [(mea("Annualised Volatility %"), False)], "Y": [(mea("Avg Daily Return %"), False)]})]
pages.append((P, "Returns and Volatility", v))

# ---- Page 4 Trading Volume
P = "pg4"
v = header(P, "Trading Volume Analysis", "Volume = number of shares traded (not money value). Zero-volume placeholder rows excluded from volume statistics.")
v += [slicer(f"{P}_s1", DATE, 20, 72, 380, 56, "Between", "Date range"), slicer(f"{P}_s2", SYMS, 420, 72, 300, 56, "Dropdown", "Stock symbol"),
      card(f"{P}_c1", "Avg Volume", 740, 72, 160, 56, "Average volume"), card(f"{P}_c2", "Max Volume", 910, 72, 160, 56, "Highest volume"), card(f"{P}_c3", "Min Volume (non-zero)", 1080, 72, 170, 56, "Lowest non-zero volume")]
v += [visual(f"{P}_v1", "lineChart", 20, 140, 820, 270, "Trading volume trend (monthly average)", {"Category": [(col("Calendar", "YearMonth"), True)], "Y": [(mea("Focus Avg Volume"), False)], "Series": [(SYMS, False)]}),
      visual(f"{P}_v2", "clusteredBarChart", 860, 140, 400, 270, "Average trading volume by stock", {"Category": [(SYMS, False)], "Y": [(mea("Focus Avg Volume"), False)]}, sort=mea("Focus Avg Volume")),
      visual(f"{P}_v3", "scatterChart", 20, 420, 560, 290, "Volume vs price movement (average volume vs average |daily return|, all symbols)",
             {"Category": [(SYMS, False)], "X": [(mea("Avg Volume"), False)], "Y": [(mea("Avg Abs Return %"), False)]}),
      visual(f"{P}_v4", "tableEx", 600, 420, 660, 290, "Highest volume observations",
             {"Values": [(col("Prices", "symbol"), False), (col("Prices", "date"), False), (col("Prices", "volume"), False), (col("Prices", "close"), False), (col("Prices", "daily_return_pct"), False)]}, sort=col("Prices", "volume"))]
pages.append((P, "Trading Volume Analysis", v))

for pid, name, vis in pages:
    pdir = RD / "pages" / pid
    (pdir / "visuals").mkdir(parents=True)
    (pdir / "page.json").write_text(json.dumps({"$schema": SCH + "page/1.0.0/schema.json", "name": pid, "displayName": name,
                                                "displayOption": "FitToPage", "height": 720, "width": 1280}, indent=2))
    for i, vj in enumerate(vis):
        vd = pdir / "visuals" / vj["name"]
        vd.mkdir()
        vj["position"]["z"] = i; vj["position"]["tabOrder"] = i
        (vd / "visual.json").write_text(json.dumps(vj, indent=2))
(RD / "pages" / "pages.json").write_text(json.dumps({"$schema": SCH + "pagesMetadata/1.0.0/schema.json",
                                                      "pageOrder": [p[0] for p in pages], "activePageName": pages[0][0]}, indent=2))
print("PBIP written; pages:", [p[1] for p in pages], "| visuals:", sum(len(p[2]) for p in pages), "| measures:", len(M))
