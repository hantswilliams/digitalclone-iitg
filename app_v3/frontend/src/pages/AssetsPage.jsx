import React, { useState, useEffect, useCallback } from 'react';
import { assetService } from '../services/assetService';
import { PlusIcon, TrashIcon, ArrowDownTrayIcon, EyeIcon } from '@heroicons/react/24/outline';
import AssetUpload from '../components/AssetUpload';
import AssetPreview from '../components/AssetPreview';

const AssetTypeFilter = ({ activeFilter, onFilterChange }) => {
  const filters = [
    { value: '', label: 'All Assets' },
    { value: 'portrait', label: 'Portraits' },
    { value: 'voice_sample', label: 'Voice Samples' },
    { value: 'script', label: 'Scripts' },
    { value: 'generated_audio', label: 'TTS Outputs' }
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

const AssetCard = ({ asset, onDelete, onView }) => {
  const getAssetTypeIcon = (type) => {
    switch (type) {
      case 'portrait':
        return '🖼️';
      case 'voice_sample':
        return '🎵';
      case 'script':
        return '📄';
      case 'generated_audio':
        return '🗣️';
      default:
        return '📁';
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Pending' },
      ready: { bg: 'bg-green-100', text: 'text-green-800', label: 'Ready' },
      processing: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Processing' },
      failed: { bg: 'bg-red-100', text: 'text-red-800', label: 'Failed' }
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getAssetTypeIcon(asset.asset_type)}</div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">{asset.filename}</h3>
            <p className="text-sm text-gray-500 capitalize">{asset.asset_type} • {formatFileSize(asset.file_size)}</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge(asset.status)}
        </div>
      </div>
      
      <div className="mt-4">
        <p className="text-sm text-gray-600">
          Uploaded: {new Date(asset.created_at).toLocaleDateString()}
        </p>
        {asset.description && (
          <p className="text-sm text-gray-600 mt-1">{asset.description}</p>
        )}
      </div>

      <div className="mt-4 flex justify-end space-x-2">
        <button
          onClick={() => onView(asset)}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          View
        </button>
        <button
          onClick={() => window.open(asset.download_url, '_blank')}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
          Download
        </button>
        <button
          onClick={() => onDelete(asset.id)}
          className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          <TrashIcon className="h-4 w-4 mr-1" />
          Delete
        </button>
      </div>
    </div>
  );
};

const AssetsPage = ({ openUploadModal = false }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(openUploadModal);
  const [previewAsset, setPreviewAsset] = useState(null);

  const loadAssets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await assetService.getAssets({ type: filter });
      
      // The backend returns {assets: [...], pagination: {...}}
      // So we need to access response.assets, not response.data
      setAssets(response.assets || []);
    } catch (err) {
      console.error('Error loading assets:', err);
      setError('Failed to load assets');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadAssets();
  }, [filter, loadAssets]);

  const handleDelete = async (assetId) => {
    if (!window.confirm('Are you sure you want to delete this asset?')) {
      return;
    }

    try {
      await assetService.deleteAsset(assetId);
      setAssets(assets.filter(asset => asset.id !== assetId));
    } catch (err) {
      setError('Failed to delete asset');
      console.error('Error deleting asset:', err);
    }
  };

  const handleView = (asset) => {
    setPreviewAsset(asset);
  };

  const handleUploadComplete = (newAsset) => {
    setAssets([newAsset, ...assets]);
    setShowUploadModal(false);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-gray-200 rounded-lg h-48"></div>
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
          <h1 className="text-2xl font-bold text-gray-900">Assets</h1>
          <p className="text-gray-600 mt-1">Manage your portraits, voice samples, and scripts</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Upload Asset
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="mb-6">
        <AssetTypeFilter activeFilter={filter} onFilterChange={setFilter} />
      </div>

      {assets.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-4xl mb-4">📁</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No assets found</h3>
          <p className="text-gray-500 mb-4">
            {filter ? `No ${filter} assets found.` : 'Get started by uploading your first asset.'}
          </p>
          <button
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Upload Asset
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assets.map((asset) => (
            <AssetCard
              key={asset.id}
              asset={asset}
              onDelete={handleDelete}
              onView={handleView}
            />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <AssetUpload
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUploadModal(false)}
        />
      )}

      {/* Asset Preview Modal */}
      {previewAsset && (
        <AssetPreview
          asset={previewAsset}
          onClose={() => setPreviewAsset(null)}
        />
      )}
    </div>
  );
};

export default AssetsPage;
