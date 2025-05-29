import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CameraIcon, 
  ArrowLeftIcon, 
  PhotoIcon,
  StopIcon,
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { assetService } from '../services/assetService';

const CapturePortraitPage = () => {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [permissions, setPermissions] = useState({ camera: null });

  // Check camera permissions
  useEffect(() => {
    const checkPermissions = async () => {
      try {
        const result = await navigator.permissions.query({ name: 'camera' });
        setPermissions(prev => ({ ...prev, camera: result.state }));
        
        result.addEventListener('change', () => {
          setPermissions(prev => ({ ...prev, camera: result.state }));
        });
      } catch (error) {
        console.warn('Permissions API not supported:', error);
      }
    };

    checkPermissions();
  }, []);

  // Start camera stream
  const startCamera = useCallback(async () => {
    try {
      setError(null);
      console.log('📷 Starting camera...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user' // Front-facing camera
        }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsStreaming(true);
        console.log('✅ Camera started successfully');
      }
    } catch (error) {
      console.error('❌ Error accessing camera:', error);
      if (error.name === 'NotAllowedError') {
        setError('Camera access denied. Please allow camera permissions and try again.');
      } else if (error.name === 'NotFoundError') {
        setError('No camera found. Please ensure you have a camera connected.');
      } else {
        setError('Failed to access camera. Please try again.');
      }
    }
  }, []);

  // Stop camera stream
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    console.log('📷 Camera stopped');
  }, []);

  // Capture photo from video stream
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw the video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob((blob) => {
      if (blob) {
        const imageUrl = URL.createObjectURL(blob);
        setCapturedImage({
          blob,
          url: imageUrl,
          timestamp: new Date().toISOString()
        });
        console.log('📸 Photo captured successfully');
      }
    }, 'image/jpeg', 0.9);
  }, []);

  // Reset and take new photo
  const retakePhoto = useCallback(() => {
    if (capturedImage?.url) {
      URL.revokeObjectURL(capturedImage.url);
    }
    setCapturedImage(null);
  }, [capturedImage]);

  // Upload captured image as asset
  const uploadPortrait = useCallback(async () => {
    if (!capturedImage) return;

    setIsUploading(true);
    setError(null);

    try {
      console.log('📤 Uploading portrait...');
      
      // Create filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `portrait-${timestamp}.jpg`;

      // Create FormData
      const formData = new FormData();
      formData.append('file', capturedImage.blob, filename);
      formData.append('asset_type', 'portrait');
      formData.append('description', 'Captured portrait photo');

      // Upload to asset service
      const result = await assetService.uploadAsset(formData);
      console.log('✅ Portrait uploaded successfully:', result);

      // Clean up and navigate
      URL.revokeObjectURL(capturedImage.url);
      stopCamera();
      
      // Navigate to assets page or show success message
      navigate('/assets', { 
        state: { 
          message: 'Portrait captured and saved successfully!',
          assetId: result.asset?.id 
        }
      });

    } catch (error) {
      console.error('❌ Error uploading portrait:', error);
      setError('Failed to save portrait. Please try again.');
    } finally {
      setIsUploading(false);
    }
  }, [capturedImage, navigate, stopCamera]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
      if (capturedImage?.url) {
        URL.revokeObjectURL(capturedImage.url);
      }
    };
  }, [stopCamera, capturedImage]);

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ArrowLeftIcon className="h-6 w-6" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Capture Portrait</h1>
            <p className="text-gray-600">Use your camera to capture a portrait photo</p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <XMarkIcon className="h-5 w-5 text-red-500 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Camera Interface */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6">
          
          {/* Camera Preview or Captured Image */}
          <div className="relative mb-6">
            <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden">
              {capturedImage ? (
                // Show captured image
                <img
                  src={capturedImage.url}
                  alt="Captured portrait"
                  className="w-full h-full object-cover"
                />
              ) : (
                // Show video stream
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                  style={{ transform: 'scaleX(-1)' }} // Mirror effect
                />
              )}
              
              {!isStreaming && !capturedImage && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center text-white">
                    <CameraIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">Camera preview will appear here</p>
                  </div>
                </div>
              )}
            </div>

            {/* Camera overlay guides */}
            {isStreaming && !capturedImage && (
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-0 border-2 border-white/30 rounded-lg"></div>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <div className="w-64 h-80 border-2 border-white/50 rounded-lg"></div>
                </div>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="flex justify-center space-x-4">
            {!isStreaming && !capturedImage && (
              <button
                onClick={startCamera}
                className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <CameraIcon className="h-5 w-5 mr-2" />
                Start Camera
              </button>
            )}

            {isStreaming && !capturedImage && (
              <>
                <button
                  onClick={capturePhoto}
                  className="flex items-center px-8 py-4 bg-green-600 text-white rounded-full hover:bg-green-700 transition-colors text-lg"
                >
                  <PhotoIcon className="h-6 w-6 mr-2" />
                  Capture Photo
                </button>
                <button
                  onClick={stopCamera}
                  className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <StopIcon className="h-5 w-5 mr-2" />
                  Stop Camera
                </button>
              </>
            )}

            {capturedImage && (
              <>
                <button
                  onClick={retakePhoto}
                  className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                >
                  <ArrowPathIcon className="h-5 w-5 mr-2" />
                  Retake
                </button>
                <button
                  onClick={uploadPortrait}
                  disabled={isUploading}
                  className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckIcon className="h-5 w-5 mr-2" />
                      Save Portrait
                    </>
                  )}
                </button>
              </>
            )}
          </div>

          {/* Camera Tips */}
          {isStreaming && !capturedImage && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-medium text-blue-900 mb-2">📸 Portrait Tips:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Position your face in the center frame</li>
                <li>• Ensure good lighting on your face</li>
                <li>• Look directly at the camera</li>
                <li>• Keep a neutral expression</li>
                <li>• Make sure your entire face is visible</li>
              </ul>
            </div>
          )}

          {/* Permission Info */}
          {permissions.camera === 'denied' && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-sm font-medium text-yellow-900 mb-2">Camera Access Required</h3>
              <p className="text-sm text-yellow-700">
                Please enable camera permissions in your browser settings to capture portraits.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Hidden canvas for image capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </div>
  );
};

export default CapturePortraitPage;
