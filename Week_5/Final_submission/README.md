# Morocco Electricity Consumption Analysis

## Project overview

This project explores electricity consumption across three zones using
MySQL for data storage, cleaning and analysis, and Power BI for
interactive visualisation. The source data contains observations sampled
at 10-minute intervals during 2017.

## Project files

-   `powerconsumption (1).csv` --- original dataset.
-   `powerconsumption_datadictionary.csv` --- source field descriptions.
-   `Morocco_Electricity_Analytical_Report.pdf` --- short analytical
    report.
-   `Business_Insights_and_Recommendations.docx` --- business insights
    and proposed actions.
-   `README_Morocco_Electricity_Analysis.md` --- this reproduction
    guide.

## Dataset

The CSV contains **52,416 records and 9 columns**: `Datetime`,
`Temperature`, `Humidity`, `WindSpeed`, `GeneralDiffuseFlows`,
`DiffuseFlows`, `PowerConsumption_Zone1`, `PowerConsumption_Zone2`, and
`PowerConsumption_Zone3`.

The supplied file covers **2017-01-01 00:00** through **2017-12-30
23:50**. The data dictionary states temperature in Celsius, wind speed
in kilometres per hour, and zone consumption in kilowatt-hours. It
describes humidity as water-vapour concentration and the diffuse-flow
fields as measures of emissions-gas diffusion into the broader and local
atmosphere. Confirm the interpretation of each 10-minute consumption
reading with the data owner before summing readings into totals.

## Requirements

-   MySQL 8.0 or later (recommended for window functions)
-   MySQL Workbench
-   Power BI Desktop
-   A compatible MySQL Connector/NET driver if Power BI requests one

## Reproducing the analysis

### 1. Create the database

``` sql
CREATE DATABASE morocco_energy_analysis;
USE morocco_energy_analysis;
```

### 2. Create and import the raw table

``` sql
CREATE TABLE power_consumption_raw (
    Datetime VARCHAR(30),
    Temperature DECIMAL(8,3),
    Humidity DECIMAL(8,3),
    WindSpeed DECIMAL(8,3),
    GeneralDiffuseFlows DECIMAL(12,3),
    DiffuseFlows DECIMAL(12,3),
    PowerConsumption_Zone1 DECIMAL(15,5),
    PowerConsumption_Zone2 DECIMAL(15,5),
    PowerConsumption_Zone3 DECIMAL(15,5)
);
```

In MySQL Workbench, use **Table Data Import Wizard** to import
`powerconsumption (1).csv` into `power_consumption_raw`. Check the
header handling and column mapping.

### 3. Create the cleaned table

Keep the raw table unchanged. Create a separate table with parsed
datetime and calendar fields:

``` sql
CREATE TABLE power_consumption_clean (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    Datetime DATETIME NOT NULL,
    Temperature DECIMAL(8,3),
    Humidity DECIMAL(8,3),
    WindSpeed DECIMAL(8,3),
    GeneralDiffuseFlows DECIMAL(12,3),
    DiffuseFlows DECIMAL(12,3),
    PowerConsumption_Zone1 DECIMAL(15,5),
    PowerConsumption_Zone2 DECIMAL(15,5),
    PowerConsumption_Zone3 DECIMAL(15,5),
    Year INT,
    Month_Num INT,
    Month_Name VARCHAR(15),
    Day INT,
    Hour INT,
    Day_Of_Week VARCHAR(15),
    Reading_Date DATE,
    INDEX idx_datetime (Datetime),
    INDEX idx_reading_date (Reading_Date)
);
```

Load it from the raw table. The format below matches month/day/year
hour:minute values, including non-padded month, day and hour:

``` sql
INSERT INTO power_consumption_clean (
    Datetime, Temperature, Humidity, WindSpeed,
    GeneralDiffuseFlows, DiffuseFlows,
    PowerConsumption_Zone1, PowerConsumption_Zone2, PowerConsumption_Zone3,
    Year, Month_Num, Month_Name, Day, Hour, Day_Of_Week, Reading_Date
)
SELECT
    STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i'),
    Temperature, Humidity, WindSpeed,
    GeneralDiffuseFlows, DiffuseFlows,
    PowerConsumption_Zone1, PowerConsumption_Zone2, PowerConsumption_Zone3,
    YEAR(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    MONTH(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    MONTHNAME(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DAY(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    HOUR(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DAYNAME(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DATE(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i'))
FROM power_consumption_raw
WHERE STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i') IS NOT NULL;
```

Test the datetime conversion on several raw values first if your import
strings differ. Do not rerun this insert into an already populated clean
table unless you intentionally clear it.

### 4. Validate the data

``` sql
-- Row count and date range
SELECT COUNT(*) AS total_records,
       MIN(Datetime) AS first_reading,
       MAX(Datetime) AS last_reading
FROM power_consumption_clean;

-- Missing values in key fields
SELECT SUM(Datetime IS NULL) AS missing_datetime,
       SUM(Temperature IS NULL) AS missing_temperature,
       SUM(Humidity IS NULL) AS missing_humidity,
       SUM(WindSpeed IS NULL) AS missing_windspeed,
       SUM(PowerConsumption_Zone1 IS NULL) AS missing_zone1,
       SUM(PowerConsumption_Zone2 IS NULL) AS missing_zone2,
       SUM(PowerConsumption_Zone3 IS NULL) AS missing_zone3
FROM power_consumption_clean;

-- Duplicate timestamps
SELECT Datetime, COUNT(*) AS occurrences
FROM power_consumption_clean
GROUP BY Datetime
HAVING COUNT(*) > 1;

-- Ten-minute interval validation (MySQL 8+)
WITH ordered_readings AS (
    SELECT Datetime, LAG(Datetime) OVER (ORDER BY Datetime) AS previous_datetime
    FROM power_consumption_clean
)
SELECT COUNT(*) AS irregular_intervals
FROM ordered_readings
WHERE previous_datetime IS NOT NULL
  AND TIMESTAMPDIFF(MINUTE, previous_datetime, Datetime) <> 10;
```

The supplied source CSV was checked during preparation: it has 0 missing
cells, 0 duplicate timestamps and 0 negative zone-consumption values. It
contains 52,415 exact 10-minute adjacent intervals out of 52,415. Re-run
the checks on your own imported clean table to verify your SQL workflow.
The file does not include 31 December 2017; do not invent readings for
that date.

### 5. Reproduce descriptive analysis

**Average consumption by zone**

``` sql
SELECT 'Zone 1' AS Zone, AVG(PowerConsumption_Zone1) AS Average_Consumption
FROM power_consumption_clean
UNION ALL
SELECT 'Zone 2', AVG(PowerConsumption_Zone2) FROM power_consumption_clean
UNION ALL
SELECT 'Zone 3', AVG(PowerConsumption_Zone3) FROM power_consumption_clean;
```

**Hourly averages**

``` sql
SELECT Hour,
       AVG(PowerConsumption_Zone1) AS Zone1_Avg,
       AVG(PowerConsumption_Zone2) AS Zone2_Avg,
       AVG(PowerConsumption_Zone3) AS Zone3_Avg
FROM power_consumption_clean
GROUP BY Hour
ORDER BY Hour;
```

**Monthly averages**

``` sql
SELECT Month_Num, Month_Name,
       AVG(PowerConsumption_Zone1) AS Zone1_Avg,
       AVG(PowerConsumption_Zone2) AS Zone2_Avg,
       AVG(PowerConsumption_Zone3) AS Zone3_Avg
FROM power_consumption_clean
GROUP BY Month_Num, Month_Name
ORDER BY Month_Num;
```

**Weekday averages**

``` sql
SELECT DAYOFWEEK(Reading_Date) AS Weekday_Num, Day_Of_Week,
       AVG(PowerConsumption_Zone1) AS Zone1_Avg,
       AVG(PowerConsumption_Zone2) AS Zone2_Avg,
       AVG(PowerConsumption_Zone3) AS Zone3_Avg
FROM power_consumption_clean
GROUP BY DAYOFWEEK(Reading_Date), Day_Of_Week
ORDER BY Weekday_Num;
```

For Pearson correlation in MySQL, use the manual formula below rather
than assuming `CORR()` is available:

``` sql
(AVG(x * y) - AVG(x) * AVG(y))
/
NULLIF(STDDEV_POP(x) * STDDEV_POP(y), 0)
```

Calculate each coefficient using the same pairwise non-NULL observations
for both variables. Correlation measures association, not causation.

### 6. Connect Power BI

1.  Open Power BI Desktop and choose **Get Data → MySQL database**.
2.  Enter your MySQL server and database `morocco_energy_analysis`.
3.  Choose **Import**, authenticate, and select
    `power_consumption_clean`.
4.  Confirm `Datetime` is Date/Time and `Reading_Date` is Date; check
    that `Year`, `Month_Num`, `Day` and `Hour` are numeric.
5.  Sort `Month_Name` by `Month_Num`. Sort weekday names by a
    weekday-number column.
6.  If Power BI requests a driver, install a compatible MySQL
    Connector/NET driver and restart Power BI.

### 7. Create Power BI measures

``` dax
Total Records =
COUNTROWS(power_consumption_clean)

Average Zone 1 =
AVERAGE(power_consumption_clean[PowerConsumption_Zone1])

Average Zone 2 =
AVERAGE(power_consumption_clean[PowerConsumption_Zone2])

Average Zone 3 =
AVERAGE(power_consumption_clean[PowerConsumption_Zone3])

Overall Average Consumption =
DIVIDE([Average Zone 1] + [Average Zone 2] + [Average Zone 3], 3)
```

The overall measure gives equal weight to the three zone averages; it is
not a sum across zones.

### 8. Build the Power BI visuals

Recommended visuals: KPI cards for record count and zone averages;
average consumption by zone; hourly and monthly line charts; weekday and
daily trends; scatter plots for temperature, humidity and wind speed
against consumption; and a line chart for GeneralDiffuseFlows and
DiffuseFlows. Add Year, Month and Day of Week slicers. Keep zone colours
consistent. For scatter plots, choose an explicit observation-level or
aggregated design and avoid accidentally collapsing all observations to
a single point.

## Results reproduced from the supplied CSV

  Measure                                      Result
  -------------------------------- ------------------
  Records                                      52,416
  First reading                      2017-01-01 00:00
  Last reading                       2017-12-30 23:50
  Average Zone 1                            32,344.97
  Average Zone 2                            21,042.51
  Average Zone 3                            17,835.41
  Highest combined-average hour                 20:00
  Lowest combined-average hour                  06:00
  Highest combined-average month                 July
  Lowest combined-average month              December

The combined hourly and monthly averages are equal-weighted averages of
the three zone averages for each period. They are not monthly energy
totals.

## Limitations and good practice

-   31 December 2017 is absent from the source file.
-   Confirm the meaning of each 10-minute kWh reading before summing
    values or using them for energy accounting.
-   Correlation does not establish causation.
-   Investigate outliers before deciding whether they are errors.
-   Preserve the raw source and document all cleaning and transformation
    decisions.
