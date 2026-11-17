
CREATE DATABASE morocco_energy_analysis;
USE morocco_energy_analysis;
SHOW DATABASES;

USE morocco_energy_analysis;

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

SELECT COUNT(*) AS total_records
FROM power_consumption_raw;

SELECT *
FROM power_consumption_raw
LIMIT 10;

DESCRIBE power_consumption_raw;
SELECT
    MIN(STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i')) AS first_record,
    MAX(STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i')) AS last_record
FROM power_consumption_raw;

SELECT
    COUNT(*) AS total_records
FROM power_consumption_raw;

SELECT
    COUNT(*) AS total_records,

    SUM(Datetime IS NULL) AS missing_datetime,
    SUM(Temperature IS NULL) AS missing_temperature,
    SUM(Humidity IS NULL) AS missing_humidity,
    SUM(WindSpeed IS NULL) AS missing_windspeed,
    SUM(GeneralDiffuseFlows IS NULL) AS missing_general_diffuse,
    SUM(DiffuseFlows IS NULL) AS missing_diffuse,
    SUM(PowerConsumption_Zone1 IS NULL) AS missing_zone1,
    SUM(PowerConsumption_Zone2 IS NULL) AS missing_zone2,
    SUM(PowerConsumption_Zone3 IS NULL) AS missing_zone3

FROM power_consumption_raw;

SELECT
    Datetime,
    COUNT(*) AS occurrences
FROM power_consumption_raw
GROUP BY Datetime
HAVING COUNT(*) > 1;

SELECT
    COUNT(*) AS duplicate_records
FROM (
    SELECT *
    FROM power_consumption_raw
    GROUP BY
        Datetime,
        Temperature,
        Humidity,
        WindSpeed,
        GeneralDiffuseFlows,
        DiffuseFlows,
        PowerConsumption_Zone1,
        PowerConsumption_Zone2,
        PowerConsumption_Zone3
    HAVING COUNT(*) > 1
) AS duplicates;

SELECT
    COUNT(*) AS total_records,
    SUM(
        STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i') IS NULL
    ) AS invalid_datetime
FROM power_consumption_raw;

WITH datetime_check AS (
    SELECT
        STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i') AS reading_time,

        LAG(
            STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i')
        ) OVER (
            ORDER BY STR_TO_DATE(Datetime, '%m/%d/%Y %H:%i')
        ) AS previous_time

    FROM power_consumption_raw
)

SELECT
    COUNT(*) AS total_intervals,

    SUM(
        TIMESTAMPDIFF(
            MINUTE,
            previous_time,
            reading_time
        ) = 10
    ) AS correct_10min_intervals,

    SUM(
        TIMESTAMPDIFF(
            MINUTE,
            previous_time,
            reading_time
        ) <> 10
    ) AS inconsistent_intervals

FROM datetime_check
WHERE previous_time IS NOT NULL;

SELECT
    'Zone 1' AS zone,
    MIN(PowerConsumption_Zone1) AS minimum_consumption,
    MAX(PowerConsumption_Zone1) AS maximum_consumption,
    AVG(PowerConsumption_Zone1) AS average_consumption

FROM power_consumption_raw

UNION ALL

SELECT
    'Zone 2',
    MIN(PowerConsumption_Zone2),
    MAX(PowerConsumption_Zone2),
    AVG(PowerConsumption_Zone2)

FROM power_consumption_raw

UNION ALL

SELECT
    'Zone 3',
    MIN(PowerConsumption_Zone3),
    MAX(PowerConsumption_Zone3),
    AVG(PowerConsumption_Zone3)

FROM power_consumption_raw;


USE morocco_energy_analysis;

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

SELECT
    Datetime AS original_datetime,
    STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i') AS converted_datetime
FROM power_consumption_raw
LIMIT 10;

SELECT
    COUNT(*) AS invalid_datetime_records
FROM power_consumption_raw
WHERE Datetime IS NULL
   OR STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i') IS NULL;

INSERT INTO power_consumption_clean (
    Datetime,
    Temperature,
    Humidity,
    WindSpeed,
    GeneralDiffuseFlows,
    DiffuseFlows,
    PowerConsumption_Zone1,
    PowerConsumption_Zone2,
    PowerConsumption_Zone3,
    Year,
    Month_Num,
    Month_Name,
    Day,
    Hour,
    Day_Of_Week,
    Reading_Date
)

SELECT
    STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i'),

    Temperature,
    Humidity,
    WindSpeed,
    GeneralDiffuseFlows,
    DiffuseFlows,

    PowerConsumption_Zone1,
    PowerConsumption_Zone2,
    PowerConsumption_Zone3,

    YEAR(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    MONTH(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    MONTHNAME(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DAY(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    HOUR(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DAYNAME(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i')),
    DATE(STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i'))

FROM power_consumption_raw

WHERE Datetime IS NOT NULL
  AND STR_TO_DATE(Datetime, '%c/%e/%Y %k:%i') IS NOT NULL;
  
SELECT
    COUNT(*) AS cleaned_records
FROM power_consumption_clean;

SELECT *
FROM power_consumption_clean
LIMIT 10;

SELECT
    COUNT(*) AS total_records,

    SUM(Datetime IS NULL) AS missing_datetime,
    SUM(Temperature IS NULL) AS missing_temperature,
    SUM(Humidity IS NULL) AS missing_humidity,
    SUM(WindSpeed IS NULL) AS missing_windspeed,
    SUM(GeneralDiffuseFlows IS NULL) AS missing_general_diffuse,
    SUM(DiffuseFlows IS NULL) AS missing_diffuse,
    SUM(PowerConsumption_Zone1 IS NULL) AS missing_zone1,
    SUM(PowerConsumption_Zone2 IS NULL) AS missing_zone2,
    SUM(PowerConsumption_Zone3 IS NULL) AS missing_zone3

FROM power_consumption_clean;

SELECT
    Datetime,
    COUNT(*) AS occurrences
FROM power_consumption_clean
GROUP BY Datetime
HAVING COUNT(*) > 1;

SELECT
    COUNT(*) AS duplicate_groups
FROM (
    SELECT
        Datetime,
        Temperature,
        Humidity,
        WindSpeed,
        GeneralDiffuseFlows,
        DiffuseFlows,
        PowerConsumption_Zone1,
        PowerConsumption_Zone2,
        PowerConsumption_Zone3
    FROM power_consumption_clean
    GROUP BY
        Datetime,
        Temperature,
        Humidity,
        WindSpeed,
        GeneralDiffuseFlows,
        DiffuseFlows,
        PowerConsumption_Zone1,
        PowerConsumption_Zone2,
        PowerConsumption_Zone3
    HAVING COUNT(*) > 1
) AS duplicates;

SELECT
    'Zone 1' AS zone,
    MIN(PowerConsumption_Zone1) AS minimum_value,
    MAX(PowerConsumption_Zone1) AS maximum_value,
    ROUND(AVG(PowerConsumption_Zone1), 2) AS average_value,
    ROUND(STDDEV(PowerConsumption_Zone1), 2) AS standard_deviation
FROM power_consumption_clean

UNION ALL

SELECT
    'Zone 2',
    MIN(PowerConsumption_Zone2),
    MAX(PowerConsumption_Zone2),
    ROUND(AVG(PowerConsumption_Zone2), 2),
    ROUND(STDDEV(PowerConsumption_Zone2), 2)
FROM power_consumption_clean

UNION ALL

SELECT
    'Zone 3',
    MIN(PowerConsumption_Zone3),
    MAX(PowerConsumption_Zone3),
    ROUND(AVG(PowerConsumption_Zone3), 2),
    ROUND(STDDEV(PowerConsumption_Zone3), 2)
FROM power_consumption_clean;

SELECT
    SUM(PowerConsumption_Zone1 < 0) AS negative_zone1,
    SUM(PowerConsumption_Zone2 < 0) AS negative_zone2,
    SUM(PowerConsumption_Zone3 < 0) AS negative_zone3
FROM power_consumption_clean;

SELECT
    Datetime,
    Year,
    Month_Num,
    Month_Name,
    Day,
    Hour,
    Day_Of_Week,
    Reading_Date
FROM power_consumption_clean
LIMIT 15;

