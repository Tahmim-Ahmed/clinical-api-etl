from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine



app = FastAPI(title="Clinical Data ETL Service", version="1.0.0")


# In-memory job storage (for demo purposes)
# In production, this would use a proper database or job queue
jobs: Dict[str, Dict[str, Any]] = {}


class ETLJobRequest(BaseModel):
    jobId: str
    filename: str
    studyId: Optional[str] = None


class ETLJobResponse(BaseModel):
    jobId: str
    status: str
    message: str


class ETLJobStatus(BaseModel):
    jobId: str
    status: str
    progress: Optional[int] = None
    message: Optional[str] = None


def process_job(job_id: str, filename: str):
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 10
        jobs[job_id]['message'] = 'Starting ETL'

        #read CSV 
        try:
            df = pd.read_csv(filename, skipinitialspace=True)
        except:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = f'Could not read file'
            jobs[job_id]['progress'] = 0
            return
    
        #validations
        if len(df) == 0:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = 'Data missing in CSV'
            jobs[job_id]['progress'] = 0
            return

        df.columns = df.columns.str.strip().str.lower()

        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 40
        jobs[job_id]['message'] = 'Cleaning data'

        #remove any trailing spaces
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

        #checks for required columns
        required = ['study_id', 'participant_id', 'measurement_type', 'value', 'timestamp', 'site_id']
        missing_cols = []
        for item in required:
            if item not in df.columns:
                missing_cols.append(item)
        if missing_cols:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = f'Missing required columns: {missing_cols}'
            jobs[job_id]['progress'] = 0
            return

        #count for invalid rows empty string or NAN 
        invalid = 0
        for i in range(len(df)):
            is_bad = False
            row = df.iloc[i]
            for col in required:
                val = row[col]
                if val is None or pd.isna(val) or (isinstance(val, str) and val.strip() == ''):
                    is_bad = True
                    break
            if is_bad:
                invalid += 1

        #return failure if more than half rows invalid
        valid_df = df.dropna(subset=required)

        if invalid > len(df) / 2:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = f'Too many invalid rows, row count: {invalid}/{len(df)}'
            jobs[job_id]['progress'] = 0
            return

        jobs[job_id]['status'] = 'running'
        jobs[job_id]['progress'] = 80
        jobs[job_id]['message'] = 'Inserting rows into database'

        #get database URL from env
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = 'DB Path not set in environment'
            jobs[job_id]['progress'] = 0
            return

        try:
            engine = create_engine(db_url)
            #insert valid rows into the clinical_measurements table
            valid_df.to_sql('clinical_measurements', engine, if_exists='append', index=False)
        except Exception as error:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['message'] = f'Database insert failed: {error}'
            jobs[job_id]['progress'] = 0
            return

        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['message'] = f'Completed: {len(valid_df)} rows inserted, {invalid} invalid rows'

    except Exception as error:
        ##catch other errors and return failure
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['message'] = f'Processing job failed, {error}'
        jobs[job_id]['progress'] = 0

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "etl"}


@app.post("/jobs", response_model=ETLJobResponse)
async def submit_job(job_request: ETLJobRequest):
    """
    Submit a new ETL job for processing
    """
    job_id = job_request.jobId
   
    # Store job in memory
    jobs[job_id] = {
        "jobId": job_id,
        "filename": job_request.filename,
        "studyId": job_request.studyId,
        "status": "running",
        "progress": 0,
        "message": "Job started"
    }
   
    # Process job
    process_job(job_id, job_request.filename)

    return ETLJobResponse(
        jobId=job_id,
        status=jobs[job_id]['status'],
        message=jobs[job_id].get('message', 'Job completed')
    )


@app.get("/jobs/{job_id}/status", response_model=ETLJobStatus)
async def get_job_status(job_id: str):
    """
    Get the current status of an ETL job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
   
    job = jobs[job_id]
    return ETLJobStatus(
        jobId=job_id,
        status=job["status"],
        progress=job.get("progress"),
        message=job.get("message")
    )


@app.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    """
    Get detailed information about an ETL job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
   
    return jobs[job_id]


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

