***TO Test APP***<br>
Testing

docker compose up --build

**Health checks**<br>
curl http://localhost:35000/health
curl http://localhost:8000/health


**Submit job**<br>
curl -X POST http://localhost:35000/api/etl/jobs -H "Content-Type: application/json" -d "{\"filename\":\"/app/data/sample_study001.csv\",\"studyId\":\"STUDY001\"}"

Copy JOB ID from response

**Job details**<br>
curl http://localhost:35000/api/etl/jobs/{job-id}

**Status**<br>
curl http://localhost:35000/api/etl/jobs/{job-id}/status

**Query via api**<br>
curl "http://localhost:35000/api/data?studyId=STUDY001"

**Submit job directly to ETL(post with your own job id)**<br>
curl -X POST http://localhost:8000/jobs -H "Content-Type: application/json" -d "{\"jobId\":\"job1\",\"filename\":\"/app/data/sample_study001.csv\",\"studyId\":\"STUDY001\"}"

**ETL job status**<br>
curl http://localhost:8000/jobs/job1/status

**DB test**<br>
docker compose exec postgres psql -U user -d clinical_data -c "SELECT COUNT(*) FROM clinical_measurements;"

**Check ETL Jobs table**<br>
docker compose exec postgres psql -U user -d clinical_data -c "SELECT id, filename, status, created_at, updated_at, completed_at FROM etl_jobs;"

