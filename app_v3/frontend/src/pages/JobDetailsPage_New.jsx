import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { jobService } from '../services/jobService';
import JobDetailsComponent from '../components/JobDetailsComponent';

const JobDetailsPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadJobDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`🔍 Loading job details for ID: ${jobId}`);
      const jobData = await jobService.getJob(jobId);
      console.log('✅ Job data loaded:', jobData);
      
      setJob(jobData.job || jobData);
      
    } catch (err) {
      console.error('❌ Error loading job details:', err);
      setError(err.message || 'Failed to load job details');
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    loadJobDetails();
  }, [loadJobDetails]);

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading job details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Job</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
        <button
          onClick={() => navigate('/jobs')}
          className="mt-4 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Jobs
        </button>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-6">
        <p className="text-center text-gray-600">Job not found</p>
        <button
          onClick={() => navigate('/jobs')}
          className="mt-4 mx-auto block inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Jobs
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/jobs')}
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Jobs
        </button>
        
        <div className="mb-4">
          <h1 className="text-3xl font-bold text-gray-900">
            {job.title || `Job ${job.id}`}
          </h1>
          {job.description && (
            <p className="text-gray-600 mt-1">{job.description}</p>
          )}
        </div>
      </div>

      {/* Job Details Component */}
      <JobDetailsComponent job={job} />
      
      {/* Quick Actions */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={loadJobDetails}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
        >
          Refresh Job Details
        </button>
      </div>
    </div>
  );
};

export default JobDetailsPage;
