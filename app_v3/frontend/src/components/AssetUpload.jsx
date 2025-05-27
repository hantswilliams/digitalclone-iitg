import React, { useState } from 'react';
import { assetService } from '../services/assetService';
import { CloudArrowUpIcon, DocumentIcon, MusicalNoteIcon, PhotoIcon } from '@heroicons/react/24/outline';

const AssetUpload = ({ onUploadComplete, onClose }) => {
  const [step, setStep] = useState('select'); // select, upload, confirm
  const [assetType, setAssetType] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const assetTypes = [
    {
      value: 'portrait',
      label: 'Portrait Image',
      description: 'Upload a portrait photo for your digital avatar',
      icon: PhotoIcon,
      accept: 'image/*',
      maxSize: 10 * 1024 * 1024, // 10MB
      formats: ['JPG', 'PNG', 'WEBP']
    },
    {
      value: 'voice_sample',
      label: 'Voice Sample',
      description: 'Upload an audio sample for voice cloning',
      icon: MusicalNoteIcon,
      accept: 'audio/*',
      maxSize: 50 * 1024 * 1024, // 50MB
      formats: ['MP3', 'WAV', 'M4A']
    },
    {
      value: 'script',
      label: 'Script File',
      description: 'Upload a text file containing your script',
      icon: DocumentIcon,
      accept: '.txt,.md,.doc,.docx',
      maxSize: 1 * 1024 * 1024, // 1MB
      formats: ['TXT', 'MD', 'DOC', 'DOCX']
    }
  ];

  const selectedAssetType = assetTypes.find(type => type.value === assetType);

  const handleAssetTypeSelect = (type) => {
    setAssetType(type);
    setStep('upload');
    setError('');
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file size
    if (selectedAssetType && file.size > selectedAssetType.maxSize) {
      setError(`File size must be less than ${(selectedAssetType.maxSize / (1024 * 1024)).toFixed(0)}MB`);
      return;
    }

    setSelectedFile(file);
    setError('');
  };

  const uploadToPresignedUrl = async (presignedUrl, file) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = Math.round((event.loaded / event.total) * 100);
          setUploadProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve();
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('PUT', presignedUrl);
      xhr.setRequestHeader('Content-Type', file.type);
      xhr.send(file);
    });
  };

  const handleUpload = async () => {
    if (!selectedFile || !assetType) return;

    try {
      setUploading(true);
      setError('');

      // Step 1: Get presigned URL
      const presignedResponse = await assetService.getPresignedUrl(
        selectedFile.name,
        selectedFile.type,
        assetType,
        selectedFile.size
      );

      // Step 2: Upload to presigned URL
      await uploadToPresignedUrl(presignedResponse.upload_url, selectedFile);

      // Step 3: Confirm the upload
      const confirmResponse = await assetService.confirmUpload(presignedResponse.asset_id);

      setStep('confirm');
      if (onUploadComplete) {
        onUploadComplete(confirmResponse.asset);
      }

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.message || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleStartOver = () => {
    setStep('select');
    setAssetType('');
    setSelectedFile(null);
    setDescription('');
    setError('');
    setUploadProgress(0);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-gray-900">
            {step === 'select' && 'Upload Asset'}
            {step === 'upload' && `Upload ${selectedAssetType?.label}`}
            {step === 'confirm' && 'Upload Complete'}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Step 1: Select Asset Type */}
        {step === 'select' && (
          <div className="space-y-4">
            <p className="text-gray-600">Choose the type of asset you want to upload:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {assetTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    onClick={() => handleAssetTypeSelect(type.value)}
                    className="p-6 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                  >
                    <Icon className="h-8 w-8 text-gray-600 mb-3" />
                    <h4 className="font-medium text-gray-900 mb-2">{type.label}</h4>
                    <p className="text-sm text-gray-600 mb-3">{type.description}</p>
                    <div className="text-xs text-gray-500">
                      <p>Supports: {type.formats.join(', ')}</p>
                      <p>Max size: {(type.maxSize / (1024 * 1024)).toFixed(0)}MB</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Step 2: Upload File */}
        {step === 'upload' && selectedAssetType && (
          <div className="space-y-6">
            
            {/* File Drop Zone */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              
              {!selectedFile ? (
                <div>
                  <p className="text-lg font-medium text-gray-900 mb-2">
                    Select {selectedAssetType.label}
                  </p>
                  <p className="text-gray-600 mb-4">
                    Choose a file or drag and drop it here
                  </p>
                  <input
                    type="file"
                    accept={selectedAssetType.accept}
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label
                    htmlFor="file-upload"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer"
                  >
                    Choose File
                  </label>
                  <p className="text-xs text-gray-500 mt-2">
                    {selectedAssetType.formats.join(', ')} up to {(selectedAssetType.maxSize / (1024 * 1024)).toFixed(0)}MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-lg font-medium text-gray-900 mb-2">Selected File</p>
                  <p className="text-gray-600 mb-2">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  <button
                    onClick={() => setSelectedFile(null)}
                    className="text-blue-600 hover:text-blue-500 text-sm"
                  >
                    Choose different file
                  </button>
                </div>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a description for this asset..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Upload Progress */}
            {uploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setStep('select')}
                disabled={uploading}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Back
              </button>
              <button
                onClick={handleUpload}
                disabled={!selectedFile || uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirmation */}
        {step === 'confirm' && (
          <div className="text-center space-y-6">
            <div className="text-6xl">✅</div>
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-2">Upload Successful!</h4>
              <p className="text-gray-600">
                Your {selectedAssetType?.label.toLowerCase()} has been uploaded successfully.
              </p>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-800 font-medium">Asset is being processed</p>
              <p className="text-green-700 text-sm">
                Your asset will be available for use once processing is complete.
              </p>
            </div>

            <div className="flex justify-center space-x-3">
              <button
                onClick={handleStartOver}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Upload Another
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AssetUpload;
