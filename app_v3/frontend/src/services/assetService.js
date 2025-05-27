import api from './api';

export const assetService = {
  // Get all user assets with optional filtering
  getAssets: async (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.type) params.append('asset_type', filters.type);
    if (filters.status) params.append('status', filters.status);
    if (filters.page) params.append('page', filters.page);
    if (filters.per_page) params.append('per_page', filters.per_page);

    const response = await api.get(`/api/assets?${params.toString()}`);
    return response.data;
  },

  // Get presigned URL for upload
  getPresignedUrl: async (filename, fileType, assetType) => {
    const response = await api.post('/api/assets/presigned-url', {
      filename,
      content_type: fileType,
      asset_type: assetType,
    });
    return response.data;
  },

  // Register uploaded asset
  registerAsset: async (assetData) => {
    const response = await api.post('/api/assets', assetData);
    return response.data;
  },

  // Get specific asset details
  getAsset: async (assetId) => {
    const response = await api.get(`/api/assets/${assetId}`);
    return response.data;
  },

  // Update asset metadata
  updateAsset: async (assetId, updateData) => {
    const response = await api.put(`/api/assets/${assetId}`, updateData);
    return response.data;
  },

  // Delete asset
  deleteAsset: async (assetId) => {
    const response = await api.delete(`/api/assets/${assetId}`);
    return response.data;
  },

  // Upload file to presigned URL
  uploadToPresignedUrl: async (presignedUrl, file) => {
    const response = await fetch(presignedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to upload file to storage');
    }

    return response;
  },
};
