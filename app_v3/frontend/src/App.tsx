import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import AssetsPage from './pages/AssetsPage';
import JobsPage from './pages/JobsPage';
import JobDetailsPage from './pages/JobDetailsPage';
import CreateVideoPage from './pages/CreateVideoPage';
import CreateAudioPage from './pages/CreateAudioPage';
import RecordAudioPage from './pages/RecordAudioPage';

function App() {

  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected Routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <AppLayout>
                  <DashboardPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/jobs" element={
              <ProtectedRoute>
                <AppLayout>
                  <JobsPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/jobs/:jobId" element={
              <ProtectedRoute>
                <AppLayout>
                  <JobDetailsPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/assets" element={
              <ProtectedRoute>
                <AppLayout>
                  <AssetsPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            {/* Assets upload route - opens upload modal */}
            <Route path="/assets/upload" element={
              <ProtectedRoute>
                <AppLayout>
                  <AssetsPage openUploadModal={true} />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/create-audio" element={
              <ProtectedRoute>
                <AppLayout>
                  <CreateAudioPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/record-audio" element={
              <ProtectedRoute>
                <AppLayout>
                  <RecordAudioPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/create-video" element={
              <ProtectedRoute>
                <AppLayout>
                  <CreateVideoPage />
                </AppLayout>
              </ProtectedRoute>
            } />
            
            {/* Alias route for /create */}
            <Route path="/create" element={<Navigate to="/create-video" replace />} />
            
            <Route path="/settings" element={
              <ProtectedRoute>
                <AppLayout>
                  <div className="p-6">
                    <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                    <p className="text-gray-600 mt-2">Settings page coming soon...</p>
                  </div>
                </AppLayout>
              </ProtectedRoute>
            } />
            
            {/* Default redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* 404 fallback */}
            <Route path="*" element={
              <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-900">404</h1>
                  <p className="text-gray-600 mt-2">Page not found</p>
                  <a href="/dashboard" className="text-primary-600 hover:text-primary-500 mt-4 inline-block">
                    Go to Dashboard
                  </a>
                </div>
              </div>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
