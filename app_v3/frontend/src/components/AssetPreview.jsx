import React, { useState, useRef, useEffect, useCallback } from 'react';
import { XMarkIcon, PlayIcon, PauseIcon, SpeakerWaveIcon } from '@heroicons/react/24/outline';

const AssetPreview = ({ asset, onClose }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [error, setError] = useState(null);
  const [textContent, setTextContent] = useState('');
  const [loading, setLoading] = useState(false);
  const audioRef = useRef(null);

  const loadTextContent = useCallback(async () => {
    if (!asset.download_url) {
      setError('No download URL available for this script');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(asset.download_url);
      if (!response.ok) {
        throw new Error('Failed to fetch script content');
      }
      const text = await response.text();
      setTextContent(text);
    } catch (err) {
      console.error('Error loading script content:', err);
      setError('Failed to load script content');
    } finally {
      setLoading(false);
    }
  }, [asset.download_url]);

  useEffect(() => {
    if (asset.asset_type === 'script') {
      loadTextContent();
    }
  }, [asset.asset_type, loadTextContent]);

  // Add ESC key handler to close modal
  useEffect(() => {
    const handleEscKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscKey);
    return () => {
      document.removeEventListener('keydown', handleEscKey);
    };
  }, [onClose]);

  const handlePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const seekTime = percent * duration;
    
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (time) => {
    if (isNaN(time)) return '0:00';
    
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const renderPreviewContent = () => {
    switch (asset.asset_type) {
      case 'portrait':
        return (
          <div className="flex justify-center items-center max-h-96 overflow-hidden">
            <img
              src={asset.download_url}
              alt={asset.filename}
              className="max-w-full max-h-full object-contain rounded-lg"
              onError={() => setError('Failed to load image')}
            />
          </div>
        );

      case 'voice_sample':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <div className="w-32 h-32 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <SpeakerWaveIcon className="w-16 h-16 text-blue-600" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {asset.filename}
              </h3>
            </div>

            <audio
              ref={audioRef}
              src={asset.download_url}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
              onError={() => setError('Failed to load audio file')}
              preload="metadata"
            />

            <div className="space-y-4">
              {/* Play/Pause Button */}
              <div className="flex justify-center">
                <button
                  onClick={handlePlayPause}
                  className="w-16 h-16 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center text-white transition-colors"
                  disabled={!duration}
                >
                  {isPlaying ? (
                    <PauseIcon className="w-8 h-8" />
                  ) : (
                    <PlayIcon className="w-8 h-8 ml-1" />
                  )}
                </button>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div
                  className="w-full h-2 bg-gray-200 rounded-full cursor-pointer"
                  onClick={handleSeek}
                >
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all duration-100"
                    style={{
                      width: duration ? `${(currentTime / duration) * 100}%` : '0%'
                    }}
                  />
                </div>
                <div className="flex justify-between text-sm text-gray-500">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 'script':
        return (
          <div className="space-y-4">
            <div className="text-center">
              <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
                <span className="text-2xl">📄</span>
              </div>
              <h3 className="text-lg font-medium text-gray-900">
                {asset.filename}
              </h3>
            </div>

            <div className="border rounded-lg p-4 max-h-96 overflow-y-auto">
              {loading ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-gray-500 mt-2">Loading script...</p>
                </div>
              ) : textContent ? (
                <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                  {textContent}
                </pre>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No content available
                </p>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <span className="text-2xl">📁</span>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {asset.filename}
            </h3>
            <p className="text-gray-500">
              Preview not available for this file type
            </p>
            <a
              href={asset.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center mt-4 px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Download File
            </a>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Asset Preview
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {asset.asset_type} • {asset.file_size && `${(asset.file_size / 1024 / 1024).toFixed(2)} MB`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error ? (
            <div className="text-center py-8">
              <div className="text-red-500 text-sm mb-4">{error}</div>
              <a
                href={asset.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Try Direct Download
              </a>
            </div>
          ) : (
            renderPreviewContent()
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Uploaded: {new Date(asset.created_at).toLocaleDateString()}
            </div>
            <div className="flex space-x-3">
              <a
                href={asset.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Download
              </a>
              <button
                onClick={onClose}
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetPreview;
