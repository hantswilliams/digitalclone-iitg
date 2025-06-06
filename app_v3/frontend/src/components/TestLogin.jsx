import React, { useState } from 'react';
import { authService } from '../services/authService';

const TestLogin = ({ onLoginSuccess }) => {
  const [credentials, setCredentials] = useState({
    email: 'test@example.com',
    password: 'TestPassword123!'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login(credentials.email, credentials.password);
      console.log('Login successful:', response);
      if (onLoginSuccess) {
        onLoginSuccess(response.user);
      }
    } catch (err) {
      setError(err.response?.data?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = () => {
    // For testing - manually set tokens from the curl response
    localStorage.setItem('access_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0ODM0OTEzOCwianRpIjoiZTA0ZTRlODktMWRhYS00NjViLTg1MjUtNTgyMzFjYWZkYTZlIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjUzIiwibmJmIjoxNzQ4MzQ5MTM4LCJjc3JmIjoiZWVmODVjNTQtNTQ1Yy00OWJiLWJjMWUtYjA5MGRiZmM0N2FmIiwiZXhwIjoxNzQ4MzUyNzM4fQ._MUJ2Eg26gzRSBMmbHFAwRpuSaSJ5o3Ir-7DHHlthkk');
    localStorage.setItem('refresh_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc0ODM0OTEzOCwianRpIjoiZDFlMjE3NGEtOTMyYi00Nzk1LTlmZTEtMjkyNjM3NzYzYTgyIiwidHlwZSI6InJlZnJlc2giLCJzdWIiOiI1MyIsIm5iZiI6MTc0ODM0OTEzOCwiY3NyZiI6ImQwNTE2NTc4LTcyYTEtNDczNS04NDc3LWE0ZTdkYTNkODBhYSIsImV4cCI6MTc1MDk0MTEzOH0.2VZgdlSaN5lGwT7CxHNhoMrRfZTbwmFyPSg2b0gKKxM');
    
    if (onLoginSuccess) {
      onLoginSuccess({
        email: 'test@example.com',
        username: 'demouser',
        first_name: 'Demo',
        last_name: 'User'
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Test Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Login to test the upload functionality
          </p>
        </div>
        
        <div className="space-y-4">
          <button
            onClick={handleQuickLogin}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            Quick Login (Demo User)
          </button>
          
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">Or login manually</span>
            </div>
          </div>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials({...credentials, email: e.target.value})}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TestLogin;
