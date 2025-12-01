import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import { DatabaseService } from './database.service';

export interface ETLJob {
  id: string;
  filename: string;
  studyId?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  errorMessage?: string;
}

export class ETLService {
  private dbService: DatabaseService;
  private etlServiceUrl: string;

  constructor() {
    this.dbService = new DatabaseService();
    this.etlServiceUrl = process.env.ETL_SERVICE_URL || 'http://etl:8000';
  }

  /**
   * Submit new ETL job
   */
  async submitJob(filename: string, studyId?: string): Promise<ETLJob> {
    const jobId = uuidv4();
    
    // Create job record in database
    const job: ETLJob = {
      id: jobId,
      filename,
      studyId,
      status: 'pending',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    await this.dbService.createETLJob(job);

    // Submit job to ETL service
    try {
      await axios.post(`${this.etlServiceUrl}/jobs`, {
        jobId,
        filename,
        studyId
      });

      // Update job status to running
      await this.dbService.updateETLJobStatus(jobId, 'running');
      job.status = 'running';
    } catch (error) {
      // Update job status to failed
      await this.dbService.updateETLJobStatus(jobId, 'failed', 'Failed to submit to ETL service');
      job.status = 'failed';
      job.errorMessage = 'Failed to submit to ETL service';
    }

    return job;
  }

  /**
   * Get ETL job by ID
   */
  async getJob(jobId: string): Promise<ETLJob | null> {
    return await this.dbService.getETLJob(jobId);
  }

  // TODO: CANDIDATE TO IMPLEMENT
  // /**
  //  * Get ETL job status from ETL service
  //  */
  async getJobStatus(jobId: string): Promise<{ status: string; progress?: number; message?: string } | null> {
    // Implementation needed:
    // 1. Validate jobId exists in database
    // 2. Call ETL service to get real-time status
    // 3. Handle connection errors gracefully
    // 4. Return formatted status response


    try {
      const job = await this.dbService.getETLJob(jobId);
        if(!job){
          return null;
        }
        //check if job is finished in db
        if(job.status=='completed' || job.status==='failed'){
          return { status: job.status, message: job?.errorMessage||"Job completed successfully"};
        }

      //if not in db and get job status from etl
      const response = await axios.get(`${this.etlServiceUrl}/jobs/${jobId}/status`, { timeout: 3000 });
      const data = response?.data;
      
      const status = data?.status || job?.status;
      const progress= data?.progress || undefined;
      const message = data?.message || undefined;

      // update db to match etl and error handling
      if (job.status!==status) {
          await this.dbService.updateETLJobStatus(jobId, status, status==='failed' ? message : undefined );
    }

      return { status, progress, message };
    } catch (error: any) {
      //throw and handle by controller
      throw error;
    }
  }
}
