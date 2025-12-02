-- Clinical Data ETL Pipeline Database Schema
-- TODO: Candidate to design and implement optimal schema


-- Basic schema provided for bootstrapping
-- Candidate should enhance with proper indexes, constraints, and optimization


-- ETL Jobs tracking table
CREATE TABLE IF NOT EXISTS etl_jobs (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    study_id VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);


--studies
CREATE TABLE IF NOT EXISTS studies (
    study_code VARCHAR(50) PRIMARY KEY,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--participants
CREATE TABLE IF NOT EXISTS participants (
    study_code VARCHAR(50) NOT NULL,
    participant_code VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (study_code, participant_code),
    FOREIGN KEY (study_code) REFERENCES studies(study_code)
);

--clinical_measurements (raw data from ETL)
CREATE TABLE IF NOT EXISTS clinical_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_id VARCHAR(50) NOT NULL,
    participant_id VARCHAR(50) NOT NULL,
    measurement_type VARCHAR(50) NOT NULL,
    value VARCHAR(100) NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    quality_score DECIMAL NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

--processed_measurements
CREATE TABLE IF NOT EXISTS processed_measurements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_code VARCHAR(50) NOT NULL,
    participant_code VARCHAR(50) NOT NULL,
    measurement_type VARCHAR(50) NOT NULL,
    agg_date TIMESTAMP NOT NULL,
    avg_value DECIMAL NOT NULL,
    min_value DECIMAL NOT NULL,
    max_value DECIMAL NOT NULL,
    measurement_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_code, participant_code)
        REFERENCES participants(study_code, participant_code)
);

--data_quality_reports
CREATE TABLE IF NOT EXISTS data_quality_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_code VARCHAR(50) NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_measurements INTEGER NOT NULL,
    low_quality_count INTEGER NOT NULL,
    avg_quality_score DECIMAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_code) REFERENCES studies(study_code)
);

--measurement_aggregations
CREATE TABLE IF NOT EXISTS measurement_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    study_code VARCHAR(50) NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    measurement_type VARCHAR(50) NOT NULL,
    total_measurements INTEGER NOT NULL,
    last_30_day_measurements INTEGER NOT NULL,
    avg_quality_score DECIMAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (study_code) REFERENCES studies(study_code),
    UNIQUE(study_code, site_id, measurement_type)
);


--Basic indexes (candidate should optimize)
CREATE INDEX IF NOT EXISTS idx_clinical_measurements_study_id ON clinical_measurements(study_id);
CREATE INDEX IF NOT EXISTS idx_clinical_measurements_participant_id ON clinical_measurements(participant_id);
CREATE INDEX IF NOT EXISTS idx_clinical_measurements_timestamp ON clinical_measurements(timestamp);
CREATE INDEX IF NOT EXISTS idx_study_type_date ON processed_measurements(study_code, measurement_type, agg_date)
CREATE INDEX IF NOT EXISTS idx_study_site_date ON data_quality_reports(study_code, site_id, report_date)

-- ETL Jobs indexes
CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_created_at ON etl_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_etl_jobs_study_id ON etl_jobs(study_id);