import axios from 'axios';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('🔄 API: 401 error detected, attempting token refresh...');
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        console.log('🔑 API: Refresh token exists?', !!refreshToken);
        
        if (refreshToken) {
          console.log('📡 API: Calling refresh endpoint...');
          const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          console.log('✅ API: Token refresh successful, new token received');
          localStorage.setItem('access_token', access_token);

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          console.log('🔄 API: Retrying original request with new token');
          return api(originalRequest);
        } else {
          console.log('❌ API: No refresh token available');
        }
      } catch (refreshError) {
        console.error('❌ API: Token refresh failed:', refreshError);
        // Refresh failed, clear tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Instead of direct window redirect, let the app handle the auth state
        // The AuthContext will detect the missing tokens and redirect appropriately
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
