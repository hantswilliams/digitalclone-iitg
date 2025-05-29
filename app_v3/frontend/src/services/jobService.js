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
    console.log('🚀 ================== JOB SERVICE: CREATE JOB ==================');
    console.log('📤 jobService.createJob called with data:', JSON.stringify(jobData, null, 2));
    console.log('🔗 API endpoint: /api/jobs/');
    console.log('⏰ Request timestamp:', new Date().toISOString());
    
    try {
      const startTime = Date.now();
      console.log('⏳ Sending API request...');
      
      const response = await api.post('/api/jobs/', jobData);
      const requestDuration = Date.now() - startTime;
      
      console.log('✅ JOB SERVICE: API Response received:');
      console.log('⏱️ Request duration:', `${requestDuration}ms`);
      console.log('📊 Response status:', response.status);
      console.log('📋 Response headers:', response.headers);
      console.log('📦 Response data:', JSON.stringify(response.data, null, 2));
      console.log('🚀 ================== JOB SERVICE: SUCCESS ==================');
      
      return response.data;
    } catch (error) {
      console.error('❌ ================== JOB SERVICE: ERROR ==================');
      console.error('💥 jobService.createJob failed:');
      console.error('📊 Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        headers: error.response?.headers,
        config: error.config ? {
          url: error.config.url,
          method: error.config.method,
          data: error.config.data
        } : null
      });
      console.error('🚀 ================== JOB SERVICE: END ERROR ==================');
      throw error;
    }
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
