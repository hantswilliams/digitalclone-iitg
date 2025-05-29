import React, { useState, useRef, useEffect } from 'react';
import { MicrophoneIcon, StopIcon, PlayIcon, PauseIcon, ArrowUpTrayIcon } from '@heroicons/react/24/outline';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/solid';
import { useAuth } from '../contexts/AuthContext';
import { assetService } from '../services/assetService';

const RecordAudioPage = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [deviceError, setDeviceError] = useState('');
  const [recordingName, setRecordingName] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioElementRef = useRef(null);

  // Check for browser support
  const isSupported = navigator.mediaDevices && navigator.mediaDevices.getUserMedia;

  useEffect(() => {
    return () => {
      // Cleanup timer on unmount
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const requestMicrophonePermission = async () => {
    try {
      console.log('🎤 Requesting microphone permission...');
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100
        } 
      });
      console.log('✅ Microphone permission granted');
      return stream;
    } catch (error) {
      console.error('❌ Microphone permission error:', error);
      if (error.name === 'NotAllowedError') {
        setDeviceError('Microphone access denied. Please allow microphone access and try again.');
      } else if (error.name === 'NotFoundError') {
        setDeviceError('No microphone found. Please connect a microphone and try again.');
      } else {
        setDeviceError('Error accessing microphone: ' + error.message);
      }
      return null;
    }
  };

  const startRecording = async () => {
    console.log('🎬 Starting audio recording...');
    
    const stream = await requestMicrophonePermission();
    if (!stream) return;

    try {
      // Reset previous recording
      setRecordedBlob(null);
      setRecordingTime(0);
      setDeviceError('');
      audioChunksRef.current = [];

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      mediaRecorderRef.current = mediaRecorder;

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = () => {
        console.log('🛑 Recording stopped');
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      mediaRecorder.start(1000); // Capture data every second
      setIsRecording(true);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      console.log('✅ Recording started');
    } catch (error) {
      console.error('❌ Recording error:', error);
      setDeviceError('Error starting recording: ' + error.message);
      // Stop all tracks if error occurs
      stream.getTracks().forEach(track => track.stop());
    }
  };

  const stopRecording = () => {
    console.log('🛑 Stopping recording...');
    
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const playRecording = () => {
    if (!recordedBlob) return;

    console.log('▶️ Playing recorded audio...');
    
    const audioUrl = URL.createObjectURL(recordedBlob);
    const audio = new Audio(audioUrl);
    audioElementRef.current = audio;

    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => {
      setIsPlaying(false);
      URL.revokeObjectURL(audioUrl);
    };
    audio.onerror = () => {
      setIsPlaying(false);
      console.error('❌ Audio playback error');
    };

    audio.play().catch(error => {
      console.error('❌ Playback error:', error);
      setIsPlaying(false);
    });
  };

  const stopPlayback = () => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  const uploadRecording = async () => {
    if (!recordedBlob || !recordingName.trim()) {
      alert('Please provide a name for your recording');
      return;
    }

    console.log('☁️ Uploading recorded audio...');
    setIsUploading(true);
    setUploadStatus('Preparing upload...');

    try {
      // Convert blob to file
      const fileName = `${recordingName.trim()}.webm`;
      const file = new File([recordedBlob], fileName, { type: 'audio/webm' });

      console.log(`📁 File created: ${fileName} (${file.size} bytes)`);
      setUploadStatus('Uploading to server...');

      // Create FormData for upload
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', 'voice_sample');
      formData.append('description', `Recorded audio: ${recordingName.trim()}`);

      console.log('📤 Uploading FormData with file and metadata...');

      // Upload using asset service
      const result = await assetService.uploadAsset(formData);
      
      console.log('✅ Upload successful:', result);
      setUploadStatus('Upload completed successfully!');
      
      // Reset form
      setRecordedBlob(null);
      setRecordingName('');
      setRecordingTime(0);
      
      // Show success message
      setTimeout(() => {
        setUploadStatus('');
        alert('Audio recording uploaded successfully! You can now use it for voice cloning.');
      }, 1000);

    } catch (error) {
      console.error('❌ Upload error:', error);
      setUploadStatus('Upload failed: ' + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  const discardRecording = () => {
    console.log('🗑️ Discarding recording...');
    setRecordedBlob(null);
    setRecordingTime(0);
    setRecordingName('');
    stopPlayback();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isSupported) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-red-800 mb-2">Browser Not Supported</h2>
          <p className="text-red-600">
            Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Safari.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Record Audio</h1>
        <p className="text-gray-600 mt-2">
          Record a voice sample directly from your browser to use for voice cloning
        </p>
      </div>

      {/* Recording Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        
        {/* Recording Controls */}
        <div className="text-center mb-8">
          
          {/* Microphone Icon & Status */}
          <div className="mb-6">
            <div className={`w-24 h-24 mx-auto rounded-full flex items-center justify-center transition-all duration-300 ${
              isRecording ? 'bg-red-100 ring-4 ring-red-200 animate-pulse' : 'bg-gray-100'
            }`}>
              <svg className={`w-12 h-12 ${isRecording ? 'text-red-600' : 'text-gray-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            
            {/* Recording Timer */}
            <div className="mt-4">
              <div className={`text-2xl font-mono font-bold ${isRecording ? 'text-red-600' : 'text-gray-600'}`}>
                {formatTime(recordingTime)}
              </div>
              {isRecording && (
                <div className="text-sm text-red-600 mt-1">Recording...</div>
              )}
            </div>
          </div>

          {/* Recording Buttons */}
          <div className="flex justify-center space-x-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isUploading}
                className="flex items-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10"/>
                </svg>
                Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="flex items-center px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12"/>
                </svg>
                Stop Recording
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {deviceError && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-red-700">{deviceError}</span>
            </div>
          </div>
        )}

        {/* Recording Preview */}
        {recordedBlob && (
          <div className="border-t pt-8">
            <h3 className="text-lg font-semibold mb-4">Recording Preview</h3>
            
            {/* Audio Controls */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={isPlaying ? stopPlayback : playRecording}
                    className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    {isPlaying ? (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                          <rect x="6" y="4" width="4" height="16"/>
                          <rect x="14" y="4" width="4" height="16"/>
                        </svg>
                        Stop
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                          <polygon points="5,3 19,12 5,21"/>
                        </svg>
                        Play
                      </>
                    )}
                  </button>
                  
                  <span className="text-gray-600">
                    Duration: {formatTime(recordingTime)}
                  </span>
                </div>
                
                <button
                  onClick={discardRecording}
                  className="text-red-600 hover:text-red-700 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Upload Form */}
            <div className="space-y-4">
              <div>
                <label htmlFor="recordingName" className="block text-sm font-medium text-gray-700 mb-2">
                  Recording Name
                </label>
                <input
                  type="text"
                  id="recordingName"
                  value={recordingName}
                  onChange={(e) => setRecordingName(e.target.value)}
                  placeholder="Enter a name for your voice recording..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  disabled={isUploading}
                />
              </div>

              {uploadStatus && (
                <div className={`p-3 rounded-lg ${
                  uploadStatus.includes('failed') || uploadStatus.includes('error') 
                    ? 'bg-red-50 text-red-700' 
                    : uploadStatus.includes('success') 
                      ? 'bg-green-50 text-green-700'
                      : 'bg-blue-50 text-blue-700'
                }`}>
                  {uploadStatus}
                </div>
              )}

              <button
                onClick={uploadRecording}
                disabled={isUploading || !recordingName.trim()}
                className="w-full flex items-center justify-center px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Uploading...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    Upload Recording
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Tips */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h4 className="font-semibold text-blue-900 mb-2">Recording Tips</h4>
          <ul className="text-blue-800 space-y-1 text-sm">
            <li>• Record in a quiet environment for best quality</li>
            <li>• Speak clearly and at a normal pace</li>
            <li>• Record at least 30 seconds for better voice cloning results</li>
            <li>• Try to record multiple samples with different emotions</li>
            <li>• Ensure your microphone is close to your mouth</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default RecordAudioPage;
