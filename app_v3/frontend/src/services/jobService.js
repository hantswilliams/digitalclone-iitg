import api from './api';

export const jobService = {
  // Get all user jobs with optional filtering
  getJobs: async (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.type) params.append('job_type', filters.type);
    if (filters.page) params.append('page', filters.page);
    if (filters.per_page) params.append('per_page', filters.per_page);
    if (filters.limit) params.append('limit', filters.limit);

    const queryString = params.toString();
    const url = queryString ? `/api/jobs/?${queryString}` : '/api/jobs/';
    const response = await api.get(url);
    return response.data;
  },

  // Get specific job details
  getJob: async (jobId) => {
    const response = await api.get(`/api/jobs/${jobId}`);
    return response.data;
  },

  // Create new job
  createJob: async (jobData) => {
    const response = await api.post('/api/jobs/', jobData);
    return response.data;
  },

  // Update job metadata
  updateJob: async (jobId, updateData) => {
    const response = await api.put(`/api/jobs/${jobId}`, updateData);
    return response.data;
  },

  // Cancel job
  cancelJob: async (jobId) => {
    const response = await api.post(`/api/jobs/${jobId}/cancel`);
    return response.data;
  },

  // Delete job
  deleteJob: async (jobId) => {
    const response = await api.delete(`/api/jobs/${jobId}`);
    return response.data;
  },

  // Get job steps
  getJobSteps: async (jobId) => {
    const response = await api.get(`/api/jobs/${jobId}/steps`);
    return response.data;
  },

  // Create job step
  createJobStep: async (jobId, stepData) => {
    const response = await api.post(`/api/jobs/${jobId}/steps`, stepData);
    return response.data;
  },

  // Poll job status (for real-time updates)
  pollJobStatus: async (jobId) => {
    const response = await api.get(`/api/jobs/${jobId}`);
    return response.data;
  },
};
