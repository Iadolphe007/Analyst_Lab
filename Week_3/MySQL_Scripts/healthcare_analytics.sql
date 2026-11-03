USE healthcare_analytics;

SHOW TABLES;
DESCRIBE patients_stage;

SELECT *
FROM patients_stage
LIMIT 5;

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

SELECT COUNT(*) AS encounters_stage_count
FROM encounters_clean;

SELECT COUNT(*) AS procedures_stage_count
FROM procedures_clean;

SELECT COUNT(*) AS procedures_stage_count
FROM procedures_stage;