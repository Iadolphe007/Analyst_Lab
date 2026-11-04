USE healthcare_analytics;


SHOW TABLES;
DESCRIBE patients_stage;

SELECT *
FROM patients_stage
LIMIT 5;
SHOW TABLES;
CREATE TABLE patients_clean AS
SELECT
    Id,
    BIRTHDATE,
    DEATHDATE,
    PREFIX,
    FIRST,
    First_Clean,
    LAST,
    Last_clean,
    MAIDEN,
    MARITAL,
    RACE,
    ETHNICITY,
    GENDER,
    BIRTHPLACE,
    ADDRESS,
    CITY,
    STATE,
    COUNTY,
    ZIP,
    LAT,
    LON,
    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP_Clean
FROM patients_stage;

SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT Id) AS unique_patients,
    SUM(ZIP_Clean IS NULL) AS missing_zip
FROM patients_clean;

SELECT
    COUNT(*) AS total_records,
    COUNT(DISTINCT Id) AS unique_patients,
    SUM(ZIP_Clean IS NULL) AS missing_zip
FROM patients_clean;

SELECT ZIP, ZIP_Clean
FROM patients_clean
WHERE ZIP IS NOT NULL
LIMIT 20;

alter TABLE encounters_stage RENAME COLUMN ï»¿Id TO Id;

CREATE TABLE encounters_clean AS
SELECT
    Id,
    START,
    STOP,
    PATIENT,
    ORGANIZATION,
    PAYER,
    ENCOUNTERCLASS,
    CODE,
    DESCRIPTION,
    BASE_ENCOUNTER_COST,
    TOTAL_CLAIM_COST,
    PAYER_COVERAGE,
    REASONCODE,
    REASONDESCRIPTION
FROM encounters_stage;

SELECT
    COUNT(*) AS total_encounters,
    COUNT(DISTINCT Id) AS unique_encounters,
    SUM(REASONCODE IS NULL OR TRIM(REASONCODE) = '') AS missing_reason_codes,
    SUM(REASONDESCRIPTION IS NULL OR TRIM(REASONDESCRIPTION) = '') AS missing_reason_descriptions
FROM encounters_clean;

-- checking unsual encounter cost

SELECT *
FROM encounters_clean
WHERE TOTAL_CLAIM_COST = 0
  AND BASE_ENCOUNTER_COST > 0;
  
CREATE TABLE procedures_clean AS
SELECT
    START,
    STOP,
    PATIENT,
    ENCOUNTER,
    CODE,
    DESCRIPTION,
    BASE_COST,
    REASONCODE,
    REASONDESCRIPTION,
    REASONDESCRIPTION_ADEDD AS REASONDESCRIPTION_ADDED
FROM procedures_stage;

--  Renaming the start column 

ALTER TABLE procedures_stage
RENAME COLUMN ï»¿START TO START;

SELECT
    COUNT(*) AS total_procedures,
    SUM(REASONCODE IS NULL OR TRIM(REASONCODE) = '') AS missing_reason_codes,
    SUM(REASONDESCRIPTION IS NULL OR TRIM(REASONDESCRIPTION) = '') AS missing_reason_descriptions
FROM procedures_clean;

ALTER TABLE payers_stage
RENAME COLUMN ï»¿Id TO Id;

CREATE TABLE payers_clean AS
SELECT
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE_HEADQUARTERED,
    ZIP,
    PHONE,
    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS Clean_ZIP
FROM payers_stage;

ALTER TABLE organizations_stage
RENAME COLUMN ï»¿Id TO Id;

CREATE TABLE organizations_clean AS
SELECT
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE,
    ZIP,
    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP_Clean,
    LAT,
    LON
FROM organizations_stage;

SELECT *
FROM organizations_clean;

-- checking duplicate

SELECT Id, COUNT(*) AS occurrences
FROM patients_clean
GROUP BY Id
HAVING COUNT(*) > 1;

SELECT Id, COUNT(*) AS occurrences
FROM encounters_clean
GROUP BY Id
HAVING COUNT(*) > 1;

SELECT
    PATIENT,
    ENCOUNTER,
    START,
    CODE,
    COUNT(*) AS occurrences
FROM procedures_clean
GROUP BY PATIENT, ENCOUNTER, START, CODE
HAVING COUNT(*) > 1;

-- checking table relationship
-- whether encounters reference patients that do not exist

SELECT COUNT(*) AS unmatched_patients
FROM encounters_clean e
LEFT JOIN patients_clean p
    ON e.PATIENT = p.Id
WHERE p.Id IS NULL;

-- whether procedures reference patients that do not exist

SELECT COUNT(*) AS unmatched_procedure_patients
FROM procedures_clean pr
LEFT JOIN patients_clean p
    ON pr.PATIENT = p.Id
WHERE p.Id IS NULL;

-- whether procedures reference encounters that do not exist

SELECT COUNT(*) AS unmatched_encounters
FROM procedures_clean pr
LEFT JOIN encounters_clean e
    ON pr.ENCOUNTER = e.Id
WHERE e.Id IS NULL;

-- check payer reference

SELECT COUNT(*) AS unmatched_payers
FROM encounters_clean e
LEFT JOIN payers_clean p
    ON e.PAYER = p.Id
WHERE e.PAYER IS NOT NULL
  AND TRIM(e.PAYER) <> ''
  AND p.Id IS NULL;
  
-- check organization reference

SELECT COUNT(*) AS unmatched_organizations
FROM encounters_clean e
LEFT JOIN organizations_clean o
    ON e.ORGANIZATION = o.Id
WHERE e.ORGANIZATION IS NOT NULL
  AND TRIM(e.ORGANIZATION) <> ''
  AND o.Id IS NULL;
  
-- date review and unsual records
-- encounters

SELECT
    e.Id,
    e.PATIENT,
    e.START,
    e.STOP,
    p.DEATHDATE,
    e.ENCOUNTERCLASS
FROM encounters_clean e
JOIN patients_clean p
    ON e.PATIENT = p.Id
WHERE p.DEATHDATE IS NOT NULL
  AND e.START > p.DEATHDATE;
  
-- checking for procedure

SELECT
    pr.PATIENT,
    pr.ENCOUNTER,
    pr.START,
    pr.STOP,
    p.DEATHDATE
FROM procedures_clean pr
JOIN patients_clean p
    ON pr.PATIENT = p.Id
WHERE p.DEATHDATE IS NOT NULL
  AND pr.START > p.DEATHDATE;
  
-- creating useful view analysis

CREATE VIEW vw_patient_demographics AS
SELECT
    GENDER,
    RACE,
    ETHNICITY,
    MARITAL,
    COUNT(*) AS patient_count
FROM patients_clean
GROUP BY GENDER, RACE, ETHNICITY, MARITAL;

CREATE VIEW vw_encounter_summary AS
SELECT
    ENCOUNTERCLASS,
    COUNT(*) AS encounter_count,
    SUM(BASE_ENCOUNTER_COST) AS total_base_cost,
    SUM(TOTAL_CLAIM_COST) AS total_claim_cost,
    SUM(PAYER_COVERAGE) AS total_payer_coverage,
    AVG(TOTAL_CLAIM_COST) AS average_claim_cost
FROM encounters_clean
GROUP BY ENCOUNTERCLASS;

CREATE VIEW vw_procedure_summary AS
SELECT
    DESCRIPTION,
    COUNT(*) AS procedure_count,
    SUM(BASE_COST) AS total_procedure_cost,
    AVG(BASE_COST) AS average_procedure_cost
FROM procedures_clean
GROUP BY DESCRIPTION;

CREATE VIEW vw_payer_summary AS
SELECT
    p.NAME AS payer_name,
    COUNT(e.Id) AS encounter_count,
    SUM(e.TOTAL_CLAIM_COST) AS total_claim_cost,
    SUM(e.PAYER_COVERAGE) AS total_coverage
FROM payers_clean p
LEFT JOIN encounters_clean e
    ON p.Id = e.PAYER
GROUP BY p.Id, p.NAME;

-- FINAL VALIDATION

SELECT 'Patients' AS table_name, COUNT(*) AS total_records
FROM patients_clean

UNION ALL

SELECT 'Encounters', COUNT(*)
FROM encounters_clean

UNION ALL

SELECT 'Procedures', COUNT(*)
FROM procedures_clean

UNION ALL

SELECT 'Payers', COUNT(*)
FROM payers_clean

UNION ALL

SELECT 'Organizations', COUNT(*)
FROM organizations_clean;

-------------------------------

-- CREATING A CLEAN WORKING TABLE/ NOT WORKING ON THE STAGED TABLE

CREATE TABLE patients_clean_v2 AS
SELECT *
FROM patients_stage;

CREATE TABLE encounters_clean_v2 AS
SELECT *
FROM encounters_stage;

CREATE TABLE procedures_clean_v2 AS
SELECT *
FROM procedures_stage;

CREATE TABLE payers_clean_v2 AS
SELECT *
FROM payers_stage;

CREATE TABLE organizations_clean_v2 AS
SELECT *
FROM organizations_stage;

-- VERIFYING THE NEW TABLES

SELECT 'Patients' AS table_name, COUNT(*) AS total_records
FROM patients_clean_v2

UNION ALL

SELECT 'Encounters', COUNT(*)
FROM encounters_clean_v2

UNION ALL

SELECT 'Procedures', COUNT(*)
FROM procedures_clean_v2

UNION ALL

SELECT 'Payers', COUNT(*)
FROM payers_clean_v2

UNION ALL

SELECT 'Organizations', COUNT(*)
FROM organizations_clean_v2;

-- Inspecting columns and data types

DESCRIBE patients_clean_v2;
DESCRIBE encounters_clean_v2;
DESCRIBE procedures_clean_v2;
DESCRIBE payers_clean_v2;
DESCRIBE organizations_clean_v2;

-- Handle missing and inconsistent values
-- Check missing values in patients

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN BIRTHDATE IS NULL OR TRIM(BIRTHDATE) = '' THEN 1 ELSE 0 END) AS missing_birthdate,
    SUM(CASE WHEN DEATHDATE IS NULL OR TRIM(DEATHDATE) = '' THEN 1 ELSE 0 END) AS missing_deathdate,
    SUM(CASE WHEN MARITAL IS NULL OR TRIM(MARITAL) = '' THEN 1 ELSE 0 END) AS missing_marital,
    SUM(CASE WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN 1 ELSE 0 END) AS missing_zip
FROM patients_clean_v2;

-- Check missing values in encounters
SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN PATIENT IS NULL OR TRIM(PATIENT) = '' THEN 1 ELSE 0 END) AS missing_patient,
    SUM(CASE WHEN PAYER IS NULL OR TRIM(PAYER) = '' THEN 1 ELSE 0 END) AS missing_payer,
    SUM(CASE WHEN TOTAL_CLAIM_COST IS NULL OR TRIM(TOTAL_CLAIM_COST) = '' THEN 1 ELSE 0 END) AS missing_claim_cost,
    SUM(CASE WHEN REASONCODE IS NULL OR TRIM(REASONCODE) = '' THEN 1 ELSE 0 END) AS missing_reasoncode
FROM encounters_clean_v2;

-- Check missing values in procedures

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN PATIENT IS NULL OR TRIM(PATIENT) = '' THEN 1 ELSE 0 END) AS missing_patient,
    SUM(CASE WHEN ENCOUNTER IS NULL OR TRIM(ENCOUNTER) = '' THEN 1 ELSE 0 END) AS missing_encounter,
    SUM(CASE WHEN BASE_COST IS NULL OR TRIM(BASE_COST) = '' THEN 1 ELSE 0 END) AS missing_base_cost,
    SUM(CASE WHEN REASONCODE IS NULL OR TRIM(REASONCODE) = '' THEN 1 ELSE 0 END) AS missing_reasoncode
FROM procedures_clean_v2;

-- Check missing values in payers 

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN NAME IS NULL OR TRIM(NAME) = '' THEN 1 ELSE 0 END) AS missing_name,
    SUM(CASE WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN 1 ELSE 0 END) AS missing_zip
FROM payers_clean_v2;

-- Check missing values in organizations

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN NAME IS NULL OR TRIM(NAME) = '' THEN 1 ELSE 0 END) AS missing_name,
    SUM(CASE WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN 1 ELSE 0 END) AS missing_zip
FROM organizations_clean_v2;

-- heck date formats

SELECT START, STOP
FROM encounters_clean_v2
LIMIT 10;

SELECT START, STOP
FROM procedures_clean_v2
LIMIT 10;

SELECT BIRTHDATE, DEATHDATE
FROM patients_clean_v2
LIMIT 10;

-- Creating the typed patients table

CREATE TABLE patients_final AS
SELECT
    Id,

    STR_TO_DATE(
        NULLIF(TRIM(BIRTHDATE), ''),
        '%c/%e/%Y'
    ) AS BIRTHDATE,

    STR_TO_DATE(
        NULLIF(TRIM(DEATHDATE), ''),
        '%c/%e/%Y'
    ) AS DEATHDATE,

    PREFIX,
    FIRST,
    First_Clean,
    LAST,
    Last_clean,
    MAIDEN,
    MARITAL,
    RACE,
    ETHNICITY,
    GENDER,
    BIRTHPLACE,
    ADDRESS,
    CITY,
    STATE,
    COUNTY,

    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP,

    LAT,
    LON

FROM patients_clean_v2;


-- Create the typed encounters table


CREATE TABLE encounters_final AS
SELECT
    Id,

    STR_TO_DATE(
        REPLACE(REPLACE(TRIM(START), 'T', ' '), 'Z', ''),
        '%Y-%m-%d %H:%i:%s'
    ) AS START,

    STR_TO_DATE(
        REPLACE(REPLACE(TRIM(STOP), 'T', ' '), 'Z', ''),
        '%Y-%m-%d %H:%i:%s'
    ) AS STOP,

    PATIENT,
    ORGANIZATION,
    PAYER,
    ENCOUNTERCLASS,
    CODE,
    DESCRIPTION,

    CAST(NULLIF(TRIM(BASE_ENCOUNTER_COST), '') AS DECIMAL(12,2))
        AS BASE_ENCOUNTER_COST,

    CAST(NULLIF(TRIM(TOTAL_CLAIM_COST), '') AS DECIMAL(12,2))
        AS TOTAL_CLAIM_COST,

    CAST(NULLIF(TRIM(PAYER_COVERAGE), '') AS DECIMAL(12,2))
        AS PAYER_COVERAGE,

    REASONCODE,
    REASONDESCRIPTION

FROM encounters_clean_v2;
DESCRIBE encounters_final;


-- Creating the typed procedures table

CREATE TABLE procedures_final AS
SELECT
    STR_TO_DATE(
        REPLACE(REPLACE(TRIM(START), 'T', ' '), 'Z', ''),
        '%Y-%m-%d %H:%i:%s'
    ) AS START,

    STR_TO_DATE(
        REPLACE(REPLACE(TRIM(STOP), 'T', ' '), 'Z', ''),
        '%Y-%m-%d %H:%i:%s'
    ) AS STOP,

    PATIENT,
    ENCOUNTER,
    CODE,
    DESCRIPTION,

    CAST(NULLIF(TRIM(BASE_COST), '') AS DECIMAL(12,2))
        AS BASE_COST,

    REASONCODE,
    REASONDESCRIPTION,

    REASONDESCRIPTION_ADEDD AS REASONDESCRIPTION_ADDED

FROM procedures_clean_v2;


-- Create the typed payers table

CREATE TABLE payers_final AS
SELECT
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE_HEADQUARTERED,

    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP,

    PHONE

FROM payers_clean_v2;

-- Create the typed organizations table

CREATE TABLE payers_final AS
SELECT
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE_HEADQUARTERED,

    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP,

    PHONE

FROM payers_clean_v2;

-- create organization final table

CREATE TABLE organizations_final AS
SELECT
    Id,
    NAME,
    ADDRESS,
    CITY,
    STATE,

    CASE
        WHEN ZIP IS NULL OR TRIM(ZIP) = '' THEN NULL
        ELSE LPAD(TRIM(ZIP), 5, '0')
    END AS ZIP,

    LAT,
    LON

FROM organizations_clean_v2;


-- Check duplicate patient IDs

SELECT Id, COUNT(*) AS occurrences
FROM patients_final
GROUP BY Id
HAVING COUNT(*) > 1;

-- Check duplicate encounter IDs

SELECT Id, COUNT(*) AS occurrences
FROM encounters_final
GROUP BY Id
HAVING COUNT(*) > 1;

-- Check duplicate procedures
SELECT PATIENT, ENCOUNTER, START, CODE, COUNT(*) AS occurrences
FROM procedures_final
GROUP BY PATIENT, ENCOUNTER, START, CODE
HAVING COUNT(*) > 1;

-- Check invalid date sequences

SELECT *
FROM encounters_final
WHERE START IS NOT NULL
  AND STOP IS NOT NULL
  AND STOP < START;

SELECT *
FROM procedures_final
WHERE START IS NOT NULL
  AND STOP IS NOT NULL
  AND STOP < START;
  
--  Check unusual encounter costs

SELECT *
FROM encounters_final
WHERE BASE_ENCOUNTER_COST < 0
   OR TOTAL_CLAIM_COST < 0
   OR PAYER_COVERAGE < 0;

-- check zero cost

SELECT *
FROM encounters_final
WHERE TOTAL_CLAIM_COST = 0
  AND BASE_ENCOUNTER_COST > 0;
  
-- Check unusually high procedure costs

SELECT *
FROM procedures_final
WHERE BASE_COST < 0
   OR BASE_COST > 100000
ORDER BY BASE_COST DESC;

-- VALIDATE RELATIONSHIP BETWEEN TABLES

-- Check encounters with missing patient references

SELECT e.PATIENT
FROM encounters_final e
LEFT JOIN patients_final p
    ON e.PATIENT = p.Id
WHERE p.Id IS NULL;

-- Check procedures with missing patient references

SELECT pr.PATIENT
FROM procedures_final pr
LEFT JOIN patients_final p
    ON pr.PATIENT = p.Id
WHERE p.Id IS NULL;

-- Check procedures with missing encounter references

SELECT pr.ENCOUNTER
FROM procedures_final pr
LEFT JOIN encounters_final e
    ON pr.ENCOUNTER = e.Id
WHERE e.Id IS NULL;

-- Check encounter payer references

SELECT e.PAYER
FROM encounters_final e
LEFT JOIN payers_final py
    ON e.PAYER = py.Id
WHERE e.PAYER IS NOT NULL
  AND TRIM(e.PAYER) <> ''
  AND py.Id IS NULL;

-- Check organization references

SELECT e.ORGANIZATION
FROM encounters_final e
LEFT JOIN organizations_final o
    ON e.ORGANIZATION = o.Id
WHERE e.ORGANIZATION IS NOT NULL
  AND TRIM(e.ORGANIZATION) <> ''
  AND o.Id IS NULL;
  
  -- FINAL VALIDATION
  
  SELECT 'Patients' AS table_name,
       (SELECT COUNT(*) FROM patients_clean_v2) AS original_count,
       (SELECT COUNT(*) FROM patients_final) AS final_count

UNION ALL

SELECT 'Encounters',
       (SELECT COUNT(*) FROM encounters_clean_v2),
       (SELECT COUNT(*) FROM encounters_final)

UNION ALL

SELECT 'Procedures',
       (SELECT COUNT(*) FROM procedures_clean_v2),
       (SELECT COUNT(*) FROM procedures_final)

UNION ALL

SELECT 'Payers',
       (SELECT COUNT(*) FROM payers_clean_v2),
       (SELECT COUNT(*) FROM payers_final)

UNION ALL

SELECT 'Organizations',
       (SELECT COUNT(*) FROM organizations_clean_v2),
       (SELECT COUNT(*) FROM organizations_final);
       
DESCRIBE patients_final;
DESCRIBE encounters_final;
DESCRIBE procedures_final;
DESCRIBE payers_final;
DESCRIBE organizations_final;

ALTER TABLE procedures_final
MODIFY PHONE VARCHAR(30);

ALTER TABLE organizations_final
MODIFY LAT DECIMAL(10,7),
MODIFY LON DECIMAL(10,7);

ALTER TABLE patients_final
MODIFY LAT DECIMAL(10,7),
MODIFY LON DECIMAL(10,7);

-- Check the standardized ZIP codes

SELECT ZIP
FROM patients_final
WHERE ZIP IS NOT NULL
  AND LENGTH(ZIP) <> 5;
  
SELECT ZIP
FROM payers_final
WHERE ZIP IS NOT NULL
  AND LENGTH(ZIP) <> 5;
  
-- DATA ANALYSIS

-- PATIENTS DEMOGRAPHICS

-- Total patients
SELECT COUNT(*) AS total_patients
FROM patients_final;

-- Gender distribution
SELECT GENDER, COUNT(*) AS patient_count
FROM patients_final
GROUP BY GENDER
ORDER BY patient_count DESC;

-- Race distribution
SELECT RACE, COUNT(*) AS patient_count
FROM patients_final
GROUP BY RACE
ORDER BY patient_count DESC;

-- Ethnicity distribution
SELECT ETHNICITY, COUNT(*) AS patient_count
FROM patients_final
GROUP BY ETHNICITY
ORDER BY patient_count DESC;

SELECT * FROM patients_final
where ETHNICITY = "non-hispanic";

-- Patients by state
SELECT STATE, COUNT(*) AS patient_count
FROM patients_final
GROUP BY STATE
ORDER BY patient_count DESC;

-- Patient age distribution

SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()) < 18
            THEN 'Under 18'
        WHEN TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()) BETWEEN 18 AND 29
            THEN '18–29'
        WHEN TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()) BETWEEN 30 AND 44
            THEN '30–44'
        WHEN TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()) BETWEEN 45 AND 59
            THEN '45–59'
        WHEN TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()) >= 60
            THEN '60+'
        ELSE 'Unknown'
    END AS age_group,
    COUNT(*) AS patient_count
FROM patients_final
GROUP BY age_group
ORDER BY MIN(TIMESTAMPDIFF(YEAR, BIRTHDATE, CURDATE()));

-- Procedure analysis

-- Total procedures
SELECT COUNT(*) AS total_procedures
FROM procedures_final;

-- Most frequent procedures
SELECT
    CODE,
    DESCRIPTION,
    COUNT(*) AS procedure_count
FROM procedures_final
GROUP BY CODE, DESCRIPTION
ORDER BY procedure_count DESC
LIMIT 10;

-- Procedures by year
SELECT
    YEAR(START) AS procedure_year,
    COUNT(*) AS procedure_count
FROM procedures_final
GROUP BY YEAR(START)
ORDER BY procedure_year;

-- Average procedure cost
SELECT
    ROUND(AVG(BASE_COST), 2) AS average_procedure_cost,
    ROUND(MIN(BASE_COST), 2) AS minimum_procedure_cost,
    ROUND(MAX(BASE_COST), 2) AS maximum_procedure_cost
FROM procedures_final;

-- Financial overview

SELECT
    ROUND(SUM(BASE_ENCOUNTER_COST), 2) AS total_base_cost,
    ROUND(SUM(TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(PAYER_COVERAGE), 2) AS total_payer_coverage,
    ROUND(AVG(TOTAL_CLAIM_COST), 2) AS average_claim_cost
FROM encounters_final;

-- Payer analysis

SELECT
    p.NAME AS payer_name,
    COUNT(e.Id) AS encounter_count,
    ROUND(SUM(e.TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(e.PAYER_COVERAGE), 2) AS total_coverage
FROM encounters_final e
LEFT JOIN payers_final p
    ON e.PAYER = p.Id
GROUP BY p.NAME
ORDER BY total_claim_cost DESC;

-- Top 10 patients by encounter volume

SELECT
    p.Id AS patient_id,
    p.GENDER,
    COUNT(e.Id) AS total_encounters
FROM patients_final p
JOIN encounters_final e
    ON p.Id = e.PATIENT
GROUP BY p.Id, p.GENDER
ORDER BY total_encounters DESC
LIMIT 10;

-- Encounter volume by gender

SELECT
    p.GENDER,
    COUNT(e.Id) AS total_encounters
FROM patients_final p
JOIN encounters_final e
    ON p.Id = e.PATIENT
GROUP BY p.GENDER
ORDER BY total_encounters DESC;

-- Average claim cost by encounter class

SELECT
    ENCOUNTERCLASS,
    COUNT(*) AS encounter_count,
    ROUND(AVG(TOTAL_CLAIM_COST), 2) AS average_claim_cost,
    ROUND(SUM(TOTAL_CLAIM_COST), 2) AS total_claim_cost
FROM encounters_final
GROUP BY ENCOUNTERCLASS
ORDER BY total_claim_cost DESC;

-- Payer coverage percentage

SELECT
    p.NAME AS payer_name,
    ROUND(SUM(e.TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(e.PAYER_COVERAGE), 2) AS total_coverage,
    ROUND(
        100 * SUM(e.PAYER_COVERAGE) /
        NULLIF(SUM(e.TOTAL_CLAIM_COST), 0),
        2
    ) AS coverage_percentage
FROM encounters_final e
LEFT JOIN payers_final p
    ON e.PAYER = p.Id
GROUP BY p.NAME
ORDER BY coverage_percentage DESC;

-- Monthly encounter trends

SELECT
    YEAR(START) AS encounter_year,
    MONTH(START) AS encounter_month,
    COUNT(*) AS encounter_count,
    ROUND(SUM(TOTAL_CLAIM_COST), 2) AS total_claim_cost
FROM encounters_final
GROUP BY YEAR(START), MONTH(START)
ORDER BY encounter_year, encounter_month;

-- Procedures and their associated encounter classes

SELECT
    e.ENCOUNTERCLASS,
    COUNT(pr.CODE) AS procedure_count,
    ROUND(AVG(pr.BASE_COST), 2) AS average_procedure_cost,
    ROUND(SUM(pr.BASE_COST), 2) AS total_procedure_cost
FROM procedures_final pr
JOIN encounters_final e
    ON pr.ENCOUNTER = e.Id
GROUP BY e.ENCOUNTERCLASS
ORDER BY procedure_count DESC;

-- Most common reasons for encounters

SELECT
    REASONDESCRIPTION,
    COUNT(*) AS encounter_count
FROM encounters_final
WHERE REASONDESCRIPTION IS NOT NULL
  AND TRIM(REASONDESCRIPTION) <> ''
GROUP BY REASONDESCRIPTION
ORDER BY encounter_count DESC
LIMIT 10;

-- Patient encounter frequency

SELECT
    COUNT(*) AS total_patients,
    SUM(CASE WHEN encounter_count = 1 THEN 1 ELSE 0 END)
        AS patients_with_one_encounter,
    SUM(CASE WHEN encounter_count > 1 THEN 1 ELSE 0 END)
        AS patients_with_multiple_encounters,
    ROUND(AVG(encounter_count), 2) AS average_encounters_per_patient
FROM (
    SELECT PATIENT, COUNT(*) AS encounter_count
    FROM encounters_final
    GROUP BY PATIENT
) AS patient_visits;

-- CREATING SQL ANALYTICAL VIEW

-- Create a patient demographics view

CREATE OR REPLACE VIEW vw_patient_demographics AS
SELECT
    GENDER,
    RACE,
    ETHNICITY,
    STATE,
    COUNT(*) AS patient_count
FROM patients_final
GROUP BY GENDER, RACE, ETHNICITY, STATE;

-- Create an encounter summary view

CREATE OR REPLACE VIEW vw_encounter_summary AS
SELECT
    ENCOUNTERCLASS,
    COUNT(*) AS encounter_count,
    ROUND(SUM(BASE_ENCOUNTER_COST), 2) AS total_base_cost,
    ROUND(SUM(TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(PAYER_COVERAGE), 2) AS total_payer_coverage,
    ROUND(AVG(TOTAL_CLAIM_COST), 2) AS average_claim_cost
FROM encounters_final
GROUP BY ENCOUNTERCLASS;

-- Create a monthly encounter trends view
CREATE OR REPLACE VIEW vw_monthly_encounter_trends AS
SELECT
    YEAR(START) AS encounter_year,
    MONTH(START) AS encounter_month,
    COUNT(*) AS encounter_count,
    ROUND(SUM(TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(PAYER_COVERAGE), 2) AS total_payer_coverage
FROM encounters_final
WHERE START IS NOT NULL
GROUP BY YEAR(START), MONTH(START);

-- Create a payer performance view

CREATE OR REPLACE VIEW vw_payer_analysis AS
SELECT
    COALESCE(p.NAME, 'Unmatched or missing payer') AS payer_name,
    COUNT(e.Id) AS encounter_count,
    ROUND(SUM(e.TOTAL_CLAIM_COST), 2) AS total_claim_cost,
    ROUND(SUM(e.PAYER_COVERAGE), 2) AS total_payer_coverage,
    ROUND(
        100 * SUM(e.PAYER_COVERAGE) /
        NULLIF(SUM(e.TOTAL_CLAIM_COST), 0),
        2
    ) AS coverage_percentage
FROM encounters_final e
LEFT JOIN payers_final p
    ON e.PAYER = p.Id
GROUP BY p.NAME;

-- Create a procedure analysis view
CREATE OR REPLACE VIEW vw_procedure_analysis AS
SELECT
    CODE,
    DESCRIPTION,
    COUNT(*) AS procedure_count,
    ROUND(SUM(BASE_COST), 2) AS total_procedure_cost,
    ROUND(AVG(BASE_COST), 2) AS average_procedure_cost
FROM procedures_final
GROUP BY CODE, DESCRIPTION;

-- Create a patient encounter frequency view

CREATE OR REPLACE VIEW vw_patient_encounter_frequency AS
SELECT
    p.Id AS patient_id,
    p.GENDER,
    p.RACE,
    p.ETHNICITY,
    COUNT(e.Id) AS encounter_count
FROM patients_final p
LEFT JOIN encounters_final e
    ON p.Id = e.PATIENT
GROUP BY p.Id, p.GENDER, p.RACE, p.ETHNICITY;

-- Create a common encounter reasons view

CREATE OR REPLACE VIEW vw_encounter_reasons AS
SELECT
    REASONCODE,
    REASONDESCRIPTION,
    COUNT(*) AS encounter_count
FROM encounters_final
WHERE REASONDESCRIPTION IS NOT NULL
  AND TRIM(REASONDESCRIPTION) <> ''
GROUP BY REASONCODE, REASONDESCRIPTION;

-- VERIFYING IF VIEW WORKS

SELECT * FROM vw_patient_demographics LIMIT 10;

SELECT * FROM vw_encounter_summary;

SELECT * FROM vw_monthly_encounter_trends LIMIT 20;

SELECT * FROM vw_payer_analysis;

SELECT * FROM vw_procedure_analysis
ORDER BY procedure_count DESC
LIMIT 10;

SELECT * FROM vw_patient_encounter_frequency LIMIT 10;

SELECT * FROM vw_encounter_reasons
ORDER BY encounter_count DESC
LIMIT 10;

SELECT
    ETHNICITY,
    COUNT(*) AS patient_count
FROM patients_final
GROUP BY ETHNICITY
ORDER BY patient_count DESC;


