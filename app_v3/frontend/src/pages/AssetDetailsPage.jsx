import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, ArrowDownTrayIcon, PlayIcon } from '@heroicons/react/24/outline';
import { assetService } from '../services/assetService';

const AssetDetailsPage = () => {
  const { assetId } = useParams();
  const navigate = useNavigate();
  const [asset, setAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAsset = async () => {
      try {
        setLoading(true);
        const response = await assetService.getAsset(assetId);
        setAsset(response);
        setError(null);
      } catch (err) {
        console.error('Error fetching asset:', err);
        setError('Failed to load asset details');
      } finally {
        setLoading(false);
      }
    };

    if (assetId) {
      fetchAsset();
    }
  }, [assetId]);

  const handleDownload = async () => {
    try {
      if (asset.download_url) {
        // Open download URL in new tab
        window.open(asset.download_url, '_blank');
      } else {
        console.error('No download URL available');
      }
    } catch (err) {
      console.error('Error downloading asset:', err);
    }
  };

  const handlePreview = async () => {
    try {
      let assetUrl = null;
      
      if (asset.preview_url) {
        assetUrl = asset.preview_url; // For images
      } else if (asset.download_url) {
        assetUrl = asset.download_url; // For audio/video
      }

      if (assetUrl) {
        window.open(assetUrl, '_blank');
      } else {
        console.error('No preview URL available');
      }
    } catch (err) {
      console.error('Error previewing asset:', err);
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const getAssetTypeColor = (assetType) => {
    const colors = {
      'GENERATED_VIDEO': 'bg-purple-100 text-purple-800',
      'GENERATED_AUDIO': 'bg-blue-100 text-blue-800',
      'VOICE_SAMPLE': 'bg-green-100 text-green-800',
      'PORTRAIT_IMAGE': 'bg-yellow-100 text-yellow-800',
      'SCRIPT_TEXT': 'bg-gray-100 text-gray-800'
    };
    return colors[assetType] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status) => {
    const colors = {
      'READY': 'bg-green-100 text-green-800',
      'PROCESSING': 'bg-yellow-100 text-yellow-800',
      'FAILED': 'bg-red-100 text-red-800',
      'PENDING': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <button
            onClick={() => navigate(-1)}
            className="mb-6 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back
          </button>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center py-12">
              <div className="text-red-500 text-xl mb-4">⚠️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {error || 'Asset Not Found'}
              </h3>
              <p className="text-gray-500">
                The requested asset could not be loaded.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate(-1)}
            className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            Back
          </button>
          
          <div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Asset Details</h1>
              <p className="text-gray-500 mt-1">Asset ID: {asset.id}</p>
            </div>
            
            <div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-3">
              {(asset.preview_url || asset.download_url) && (
                <button
                  onClick={handlePreview}
                  className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <PlayIcon className="h-4 w-4 mr-2" />
                  Preview
                </button>
              )}
              
              {asset.download_url && (
                <button
                  onClick={handleDownload}
                  className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                  Download
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Asset Information Card */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Asset Information</h2>
          </div>
          
          <div className="px-6 py-4">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">Filename</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">
                  {asset.original_filename || asset.filename}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Asset Type</dt>
                <dd className="mt-1">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getAssetTypeColor(asset.asset_type)}`}>
                    {asset.asset_type?.replace('_', ' ')}
                  </span>
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Status</dt>
                <dd className="mt-1">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(asset.status)}`}>
                    {asset.status}
                  </span>
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">File Size</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatFileSize(asset.file_size)}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">MIME Type</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">
                  {asset.mime_type || 'Unknown'}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">File Extension</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">
                  {asset.file_extension || 'Unknown'}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatDate(asset.created_at)}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Updated</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {formatDate(asset.updated_at)}
                </dd>
              </div>
              
              {asset.description && (
                <div className="sm:col-span-2">
                  <dt className="text-sm font-medium text-gray-500">Description</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {asset.description}
                  </dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* Storage Information Card */}
        <div className="bg-white rounded-lg shadow mt-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Storage Information</h2>
          </div>
          
          <div className="px-6 py-4">
            <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
              <div>
                <dt className="text-sm font-medium text-gray-500">Storage Bucket</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">
                  {asset.storage_bucket || 'Unknown'}
                </dd>
              </div>
              
              <div>
                <dt className="text-sm font-medium text-gray-500">Storage Path</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono break-all">
                  {asset.storage_path || 'Unknown'}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetDetailsPage;
