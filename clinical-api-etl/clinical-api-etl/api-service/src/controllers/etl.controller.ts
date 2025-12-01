import { Request, Response, NextFunction } from 'express';
import { ETLService } from '../services/etl.service';
import { successResponse, errorResponse } from '../utils/response';

export class ETLController {
  private etlService: ETLService;

  constructor() {
    this.etlService = new ETLService();
  }

  /**
   * Submit new ETL job
   * POST /api/etl/jobs
   */
  submitJob = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { filename, studyId } = req.body;

      if (!filename) {
        errorResponse(res, 'filename is required', 400);
        return;
      }

      const job = await this.etlService.submitJob(filename, studyId);
      successResponse(res, job, 'ETL job submitted successfully');
    } catch (error) {
      next(error);
    }
  };

  /**
   * Get ETL job details
   * GET /api/etl/jobs/:id
   */
  getJob = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const { id } = req.params;
      const job = await this.etlService.getJob(id);
      
      if (!job) {
        errorResponse(res, 'Job not found', 404);
        return;
      }

      successResponse(res, job, 'Job retrieved successfully');
    } catch (error) {
      next(error);
    }
  };

  // TODO: CANDIDATE TO IMPLEMENT
  // /**
  //  * Get ETL job status
  //  * GET /api/etl/jobs/:id/status
  //  */
  getJobStatus = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    // Implementation needed by candidate
    // Should integrate with ETL service to get real-time status
    // Handle error cases (invalid job ID, connection issues)
    try{
      const{id}= req.params;
      const status= await this.etlService.getJobStatus(id)

      //handle errors
      if(!status){
        errorResponse(res, 'Job status not found', 404);
        return;
        //send message on failure
      }else if(status.status === 'failed'){
        successResponse(res, status, 'Job status retrieval failed');
        return;
      }
      //return success
      successResponse(res, status, 'Job status retrieved successfully');
    }catch(error: any){
      //connection errors
      const statusCode = (error?.code?.includes('ECONN') || error?.code === 'ETIMEDOUT' ? 503 : 500) 
      const statusMessage = (statusCode === 503 ? 'ETL Connection Error' : 'Internal Server Error')
      errorResponse(res, statusMessage, statusCode);     
    }
  };
}
