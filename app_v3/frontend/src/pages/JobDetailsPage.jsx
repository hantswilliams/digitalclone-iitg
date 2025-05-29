import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PlayIcon, 
  ArrowDownTrayIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { jobService } from '../services/jobService';
import { assetService } from '../services/assetService';

const JobDetailsPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assets, setAssets] = useState({});

  const loadRelatedAssets = useCallback(async (jobData) => {
    try {
      const assetIds = new Set();
      
      // Collect asset IDs from job parameters
      if (jobData.parameters?.portrait_asset_id) {
        assetIds.add(jobData.parameters.portrait_asset_id);
      }
      if (jobData.parameters?.voice_asset_id) {
        assetIds.add(jobData.parameters.voice_asset_id);
      }
      if (jobData.parameters?.audio_asset_id) {
        assetIds.add(jobData.parameters.audio_asset_id);
      }
      
      // Add result asset ID if exists
      if (jobData.result_asset_id) {
        assetIds.add(jobData.result_asset_id);
      }
      
      // Add asset_ids array if exists
      if (jobData.asset_ids && Array.isArray(jobData.asset_ids)) {
        jobData.asset_ids.forEach(id => assetIds.add(id));
      }

      console.log(`🔍 Loading ${assetIds.size} related assets:`, Array.from(assetIds));
      
      // Load all assets
      const assetPromises = Array.from(assetIds).map(async (assetId) => {
        try {
          const asset = await assetService.getAsset(assetId);
          return { id: assetId, data: asset };
        } catch (error) {
          console.warn(`⚠️ Could not load asset ${assetId}:`, error);
          return { id: assetId, data: null };
        }
      });

      const assetResults = await Promise.all(assetPromises);
      const assetsMap = {};
      assetResults.forEach(({ id, data }) => {
        assetsMap[id] = data;
      });
      
      console.log('✅ Assets loaded:', assetsMap);
      setAssets(assetsMap);
    } catch (error) {
      console.error('❌ Error loading related assets:', error);
    }
  }, []);

  const loadJobDetails = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`🔍 Loading job details for ID: ${jobId}`);
      const jobData = await jobService.getJob(jobId);
      console.log('✅ Job data loaded:', jobData);
      
      setJob(jobData);
      
      // Load related assets
      await loadRelatedAssets(jobData);
      
    } catch (err) {
      console.error('❌ Error loading job details:', err);
      setError(err.message || 'Failed to load job details');
    } finally {
      setLoading(false);
    }
  }, [jobId, loadRelatedAssets]);

  useEffect(() => {
    loadJobDetails();
  }, [loadJobDetails]);

  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'processing':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const downloadAsset = async (asset) => {
    try {
      console.log(`📥 Downloading asset: ${asset.original_filename}`);
      
      // Create a temporary download link
      const response = await fetch(asset.storage_url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = asset.original_filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      console.log('✅ Download completed');
    } catch (error) {
      console.error('❌ Download failed:', error);
      alert('Failed to download file');
    }
  };

  const previewAsset = (asset) => {
    if (asset.storage_url) {
      window.open(asset.storage_url, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
        <p className="text-center text-gray-600 mt-4">Loading job details...</p>
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
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{job.title}</h1>
            <p className="text-gray-600 mt-1">{job.description}</p>
          </div>
          <div className="flex items-center space-x-3">
            {getStatusIcon(job.status)}
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
              {job.status}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Information */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Information</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Job ID</dt>
                <dd className="text-sm text-gray-900 font-mono">{job.id}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Type</dt>
                <dd className="text-sm text-gray-900">{job.job_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Priority</dt>
                <dd className="text-sm text-gray-900">{job.priority}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="text-sm text-gray-900">
                  {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Started</dt>
                <dd className="text-sm text-gray-900">
                  {job.started_at ? new Date(job.started_at).toLocaleString() : 'Not started'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Completed</dt>
                <dd className="text-sm text-gray-900">
                  {job.completed_at ? new Date(job.completed_at).toLocaleString() : 'Not completed'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Duration</dt>
                <dd className="text-sm text-gray-900">{formatDuration(job.duration)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Progress</dt>
                <dd className="text-sm text-gray-900">{job.progress_percentage || 0}%</dd>
              </div>
            </dl>
          </div>

          {/* Parameters */}
          {job.parameters && Object.keys(job.parameters).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Parameters</h2>
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(job.parameters, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Error Information */}
          {job.status === 'failed' && job.error_info && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-lg font-semibold text-red-900 mb-4">Error Information</h2>
              <div className="bg-red-100 rounded-md p-4">
                <pre className="text-sm text-red-700 whitespace-pre-wrap overflow-x-auto">
                  {typeof job.error_info === 'string' ? job.error_info : JSON.stringify(job.error_info, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Results */}
          {job.results && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Results</h2>
              <div className="bg-gray-50 rounded-md p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(job.results, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Result Asset */}
          {job.result_asset_id && assets[job.result_asset_id] && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Result</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    {assets[job.result_asset_id].original_filename}
                  </span>
                  <span className="text-xs text-gray-500">
                    {assets[job.result_asset_id].asset_type}
                  </span>
                </div>
                <div className="text-sm text-gray-600">
                  {formatFileSize(assets[job.result_asset_id].file_size)}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => previewAsset(assets[job.result_asset_id])}
                    className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <EyeIcon className="h-4 w-4 mr-1" />
                    Preview
                  </button>
                  <button
                    onClick={() => downloadAsset(assets[job.result_asset_id])}
                    className="flex-1 inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                    Download
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Input Assets */}
          {Object.keys(assets).length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Assets</h3>
              <div className="space-y-4">
                {Object.entries(assets).map(([assetId, asset]) => {
                  if (!asset || assetId === job.result_asset_id) return null;
                  
                  return (
                    <div key={assetId} className="border border-gray-200 rounded-md p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 truncate">
                          {asset.original_filename}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">
                          {asset.asset_type}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 mb-2">
                        {formatFileSize(asset.file_size)}
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => previewAsset(asset)}
                          className="flex-1 inline-flex items-center justify-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <EyeIcon className="h-3 w-3 mr-1" />
                          View
                        </button>
                        <button
                          onClick={() => downloadAsset(asset)}
                          className="flex-1 inline-flex items-center justify-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                        >
                          <ArrowDownTrayIcon className="h-3 w-3 mr-1" />
                          Download
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick Actions */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => window.location.reload()}
                className="w-full inline-flex items-center justify-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <ClockIcon className="h-4 w-4 mr-2" />
                Refresh Status
              </button>
              
              {job.status === 'completed' && job.job_type === 'full_pipeline' && (
                <button
                  onClick={() => navigate('/create-video')}
                  className="w-full inline-flex items-center justify-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Create Another Video
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobDetailsPage;
