import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { assetService } from '../services/assetService';

const JobDetailsComponent = ({ job, className = "" }) => {
  const [assets, setAssets] = useState({});
  const [loadingAssets, setLoadingAssets] = useState(false);

  const loadRelatedAssets = useCallback(async (jobData) => {
    try {
      setLoadingAssets(true);
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
    } finally {
      setLoadingAssets(false);
    }
  }, []);

  useEffect(() => {
    if (job) {
      loadRelatedAssets(job);
    }
  }, [job, loadRelatedAssets]);

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

  if (!job) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">No job data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Job Overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Job Information</h2>
          <div className="flex items-center space-x-2">
            {getStatusIcon(job.status)}
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
              {job.status}
            </span>
          </div>
        </div>
        
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
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="text-sm text-gray-900">{job.status}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Priority</dt>
            <dd className="text-sm text-gray-900">{job.priority}</dd>
          </div>
          {job.progress_percentage !== undefined && (
            <div>
              <dt className="text-sm font-medium text-gray-500">Progress</dt>
              <dd className="text-sm text-gray-900">{job.progress_percentage}%</dd>
            </div>
          )}
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd className="text-sm text-gray-900">
              {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
            </dd>
          </div>
        </dl>
      </div>

      {/* Asset Information */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Asset Information</h3>
        
        {loadingAssets ? (
          <div className="flex items-center justify-center py-4">
            <ClockIcon className="h-5 w-5 text-blue-500 animate-spin mr-2" />
            <span className="text-sm text-gray-600">Loading assets...</span>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 mb-2">Associated Assets</dt>
              {job.asset_ids && job.asset_ids.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {job.asset_ids.map((assetId) => {
                    const asset = assets[assetId];
                    return (
                      <Link
                        key={assetId}
                        to={`/assets/${assetId}`}
                        className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                        title={asset ? `${asset.asset_type} - ${asset.filename}` : `Asset ${assetId}`}
                      >
                        {assetId}
                        {asset && (
                          <span className="ml-1 text-xs text-blue-600">
                            ({asset.asset_type})
                          </span>
                        )}
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-gray-500 italic">No assets associated</p>
              )}
            </div>

            {/* Result Asset ID */}
            {job.result_asset_id && (
              <div>
                <dt className="text-sm font-medium text-gray-500 mb-2">Result Asset</dt>
                <Link
                  to={`/assets/${job.result_asset_id}`}
                  className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                >
                  {job.result_asset_id}
                  <span className="ml-1 text-xs text-green-600">(result)</span>
                </Link>
              </div>
            )}

            {/* Output Video ID */}
            {job.output_video_id && (
              <div>
                <dt className="text-sm font-medium text-gray-500 mb-2">Output Video</dt>
                <Link
                  to={`/assets/${job.output_video_id}`}
                  className="inline-flex items-center px-3 py-1 rounded-md text-sm font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
                >
                  {job.output_video_id}
                  <span className="ml-1 text-xs text-purple-600">(video)</span>
                </Link>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Parameters */}
      {job.job_parameters && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Parameters</h3>
          <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded border overflow-x-auto">
            {JSON.stringify(job.job_parameters, null, 2)}
          </pre>
        </div>
      )}

      {/* Results */}
      {job.result_data && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Results</h3>
          <pre className="text-sm text-gray-900 bg-gray-50 p-3 rounded border overflow-x-auto">
            {JSON.stringify(job.result_data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default JobDetailsComponent;
