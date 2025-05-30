import api from './api';

export const assetService = {
  // Get all user assets with optional filtering
  getAssets: async (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.type) params.append('asset_type', filters.type);
    if (filters.status) params.append('status', filters.status);
    if (filters.page) params.append('page', filters.page);
    if (filters.per_page) params.append('per_page', filters.per_page);

    // Ensure we use the correct endpoint with trailing slash
    const queryString = params.toString();
    const url = queryString ? `/api/assets/?${queryString}` : '/api/assets/';
    
    try {
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Error fetching assets:', error);
      throw error;
    }
  },

  // Get presigned URL for upload
  getPresignedUrl: async (filename, fileType, assetType, fileSize) => {
    const response = await api.post('/api/assets/presigned-upload', {
      filename,
      content_type: fileType,
      asset_type: assetType,
      file_size: fileSize,
    });
    return response.data;
  },

  // Confirm uploaded asset
  confirmUpload: async (assetId) => {
    const response = await api.post(`/api/assets/${assetId}/confirm-upload`);
    return response.data;
  },

  // Get specific asset details
  getAsset: async (assetId) => {
    const response = await api.get(`/api/assets/${assetId}`);
    // Backend returns {asset: asset_dict}, extract just the asset
    return response.data.asset;
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

  // Upload asset file directly (simpler than presigned URL flow)
  uploadAsset: async (formData) => {
    const response = await api.post('/api/assets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
