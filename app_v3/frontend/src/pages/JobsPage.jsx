import React, { useState, useEffect, useCallback } from 'react';
import { jobService } from '../services/jobService';
import { StopIcon, EyeIcon, TrashIcon } from '@heroicons/react/24/outline';

const JobStatusFilter = ({ activeFilter, onFilterChange }) => {
  const filters = [
    { value: '', label: 'All Jobs' },
    { value: 'pending', label: 'Pending' },
    { value: 'running', label: 'Running' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  return (
    <div className="flex space-x-2">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            activeFilter === filter.value
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

const JobTypeFilter = ({ activeFilter, onFilterChange }) => {
  const filters = [
    { value: '', label: 'All Types' },
    { value: 'voice_clone', label: 'Voice Clone' },
    { value: 'text_to_speech', label: 'Text to Speech' },
    { value: 'video_generation', label: 'Video Generation' },
    { value: 'full_pipeline', label: 'Full Pipeline' }
  ];

  return (
    <div className="flex space-x-2">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            activeFilter === filter.value
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

const ProgressBar = ({ progress, status }) => {
  const getProgressColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-gray-500';
      case 'running':
        return 'bg-blue-500';
      default:
        return 'bg-gray-300';
    }
  };

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full transition-all duration-300 ${getProgressColor()}`}
        style={{ width: `${Math.max(0, Math.min(100, progress || 0))}%` }}
      ></div>
    </div>
  );
};

const JobCard = ({ job, onCancel, onView, onDelete }) => {
  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending', icon: '⏳' },
      running: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Running', icon: '▶️' },
      completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed', icon: '✅' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed', icon: '❌' },
      cancelled: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Cancelled', icon: '⏹️' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        <span className="mr-1">{config.icon}</span>
        {config.label}
      </span>
    );
  };

  const getPriorityBadge = (priority) => {
    const priorityConfig = {
      low: { bg: 'bg-gray-100', text: 'text-gray-800' },
      normal: { bg: 'bg-blue-100', text: 'text-blue-800' },
      high: { bg: 'bg-orange-100', text: 'text-orange-800' },
      urgent: { bg: 'bg-red-100', text: 'text-red-800' }
    };

    const config = priorityConfig[priority] || priorityConfig.normal;
    
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${config.bg} ${config.text}`}>
        {priority.toUpperCase()}
      </span>
    );
  };

  const getJobTypeIcon = (type) => {
    switch (type) {
      case 'voice_clone':
        return '🎤';
      case 'text_to_speech':
        return '🗣️';
      case 'video_generation':
        return '🎬';
      case 'full_pipeline':
        return '🚀';
      default:
        return '⚙️';
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!startTime) return 'Not started';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const duration = Math.floor((end - start) / 1000);
    
    if (duration < 60) return `${duration}s`;
    if (duration < 3600) return `${Math.floor(duration / 60)}m ${duration % 60}s`;
    return `${Math.floor(duration / 3600)}h ${Math.floor((duration % 3600) / 60)}m`;
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getJobTypeIcon(job.job_type)}</div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              {job.description || `${job.job_type.replace('_', ' ').toUpperCase()} Job`}
            </h3>
            <p className="text-sm text-gray-500">ID: {job.id}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getPriorityBadge(job.priority)}
          {getStatusBadge(job.status)}
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress</span>
          <span>{job.progress || 0}%</span>
        </div>
        <ProgressBar progress={job.progress} status={job.status} />
      </div>

      <div className="text-sm text-gray-600 space-y-1">
        <p>Created: {new Date(job.created_at).toLocaleString()}</p>
        <p>Duration: {formatDuration(job.started_at, job.completed_at)}</p>
        {job.progress_message && (
          <p className="text-blue-600 font-medium">Status: {job.progress_message}</p>
        )}
      </div>

      <div className="mt-4 flex justify-end space-x-2">
        <button
          onClick={() => onView(job)}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          View Details
        </button>
        
        {(job.status === 'pending' || job.status === 'running') && (
          <button
            onClick={() => onCancel(job.id)}
            className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <StopIcon className="h-4 w-4 mr-1" />
            Cancel
          </button>
        )}
        
        {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
          <button
            onClick={() => onDelete(job.id)}
            className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
          >
            <TrashIcon className="h-4 w-4 mr-1" />
            Delete
          </button>
        )}
      </div>
    </div>
  );
};

const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);

  const loadJobs = useCallback(async () => {
    try {
      setLoading(true);
      const filters = {};
      if (statusFilter) filters.status = statusFilter;
      if (typeFilter) filters.type = typeFilter;
      
      const response = await jobService.getJobs(filters);
      setJobs(response.jobs || []);
    } catch (err) {
      setError('Failed to load jobs');
      console.error('Error loading jobs:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter]);

  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  const handleCancel = async (jobId) => {
    if (!window.confirm('Are you sure you want to cancel this job?')) {
      return;
    }

    try {
      console.log('Cancelling job:', jobId);
      
      // Clear previous messages
      setError(null);
      setSuccess(null);
      
      // Optimistically update the job status in local state
      setJobs(prevJobs => 
        prevJobs.map(job => 
          job.id === jobId 
            ? { ...job, status: 'cancelled', updated_at: new Date().toISOString() }
            : job
        )
      );

      // Cancel the job on the server
      const response = await jobService.cancelJob(jobId);
      console.log('Job cancelled successfully:', response);
      
      // Show success message
      setSuccess(`Job #${jobId} has been cancelled successfully`);
      
      // Reload to get the actual server state
      await loadJobs();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      console.error('Error canceling job:', err);
      setError('Failed to cancel job');
      setSuccess(null);
      
      // Reload jobs to restore correct state on error
      await loadJobs();
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }

    try {
      console.log('🗑️ Deleting job:', jobId);
      
      // Optimistically update UI
      setJobs(prevJobs => prevJobs.filter(job => job.id !== jobId));
      
      // Call backend delete endpoint
      await jobService.deleteJob(jobId);
      
      console.log('✅ Job deleted successfully:', jobId);
      setSuccess('Job deleted successfully');
      
      // Auto-dismiss success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      console.error('❌ Error deleting job:', err);
      
      // Revert optimistic update by refreshing the job list
      loadJobs();
      
      if (err.response?.status === 400) {
        setError(err.response.data.message || 'Cannot delete running job. Cancel it first.');
      } else if (err.response?.status === 404) {
        setError('Job not found');
      } else {
        setError('Failed to delete job');
      }
    }
  };

  const handleView = async (job) => {
    try {
      const jobDetails = await jobService.getJob(job.id);
      setSelectedJob(jobDetails.job);
    } catch (err) {
      setError('Failed to load job details');
      console.error('Error loading job details:', err);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-lg h-64"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="text-gray-600 mt-1">Monitor your video generation jobs</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
          <p className="text-green-600">{success}</p>
        </div>
      )}

      <div className="mb-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Status</label>
          <JobStatusFilter activeFilter={statusFilter} onFilterChange={setStatusFilter} />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Type</label>
          <JobTypeFilter activeFilter={typeFilter} onFilterChange={setTypeFilter} />
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">⚙️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
          <p className="text-gray-500 mb-4">
            {statusFilter || typeFilter 
              ? 'No jobs match your current filters.'
              : 'You haven\'t created any jobs yet. Get started by creating a video!'
            }
          </p>
          <a
            href="/create-video"
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Create Video
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onCancel={handleCancel}
              onView={handleView}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <h3 className="text-lg font-medium mb-4">Job Details</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Job ID</label>
                  <p className="text-sm text-gray-900">{selectedJob.id}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Type</label>
                  <p className="text-sm text-gray-900">{selectedJob.job_type}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <p className="text-sm text-gray-900">{selectedJob.status}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Priority</label>
                  <p className="text-sm text-gray-900">{selectedJob.priority}</p>
                </div>
              </div>
              
              {selectedJob.job_parameters && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Parameters</label>
                  <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded border overflow-x-auto">
                    {JSON.stringify(selectedJob.job_parameters, null, 2)}
                  </pre>
                </div>
              )}
              
              {selectedJob.result_data && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Result</label>
                  <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded border overflow-x-auto">
                    {JSON.stringify(selectedJob.result_data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setSelectedJob(null)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsPage;
