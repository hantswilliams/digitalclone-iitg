import React, { useState, useRef, useEffect } from 'react';
import { jobService } from '../services/jobService';
import { assetService } from '../services/assetService';
import { useScriptGeneration } from '../hooks/useScriptGeneration';
import { 
  MicrophoneIcon, 
  DocumentTextIcon, 
  SparklesIcon,
  PlayIcon,
  StopIcon,
  CloudArrowUpIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const CreateAudioPage = () => {
  const [textInput, setTextInput] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [audioPreview, setAudioPreview] = useState(null);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isPlayingPreview, setIsPlayingPreview] = useState(false);
  
  // New state for existing voice samples
  const [existingVoiceSamples, setExistingVoiceSamples] = useState([]);
  const [selectedVoiceSample, setSelectedVoiceSample] = useState(null);
  const [loadingVoiceSamples, setLoadingVoiceSamples] = useState(false);
  const [voiceSelectionMode, setVoiceSelectionMode] = useState('upload'); // 'upload' or 'existing'
  
  // Use shared script generation hook
  const { generateScript, isGenerating: isGeneratingScript, generationError, clearError } = useScriptGeneration();
  
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);

  // Load existing voice samples on component mount
  useEffect(() => {
    loadExistingVoiceSamples();
  }, []);

  // Handle generation error from shared hook
  useEffect(() => {
    if (generationError) {
      setError(generationError);
    }
  }, [generationError]);

  const loadExistingVoiceSamples = async () => {
    setLoadingVoiceSamples(true);
    try {
      // Get all audio assets and filter for voice samples on frontend
      // to handle any case sensitivity issues
      const response = await assetService.getAssets({
        status: 'ready'
      });
      
      if (response.assets) {
        // Filter for voice samples (handle both voice_sample and Voice_sample)
        const voiceSamples = response.assets.filter(asset => 
          asset.asset_type && 
          asset.asset_type.toLowerCase() === 'voice_sample'
        );
        setExistingVoiceSamples(voiceSamples);
      }
    } catch (err) {
      console.error('Failed to load existing voice samples:', err);
      // Don't show error for this as it's not critical
    } finally {
      setLoadingVoiceSamples(false);
    }
  };

  const handleVoiceSelectionModeChange = (mode) => {
    setVoiceSelectionMode(mode);
    // Clear previous selections when switching modes
    if (mode === 'upload') {
      setSelectedVoiceSample(null);
    } else {
      setAudioFile(null);
      setAudioPreview(null);
      if (audioRef.current) {
        audioRef.current.pause();
        setIsPlayingPreview(false);
      }
    }
    setError(null);
  };

  const handleVoiceSampleSelect = (voiceSample) => {
    setSelectedVoiceSample(voiceSample);
    setError(null);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Validate file type
      const validTypes = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg'];
      if (!validTypes.includes(file.type)) {
        setError('Please upload a valid audio file (WAV, MP3, or OGG)');
        return;
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (file.size > maxSize) {
        setError('Audio file must be smaller than 10MB');
        return;
      }

      setAudioFile(file);
      setError(null);

      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setAudioPreview(previewUrl);
    }
  };

  const handleGenerateScript = async () => {
    if (!textInput.trim()) {
      setError('Please provide some context or topic for script generation');
      return;
    }

    setError(null);
    clearError(); // Clear any previous generation errors

    try {
      console.log('🎬 Generating script via LLM...');
      
      // Use shared script generation hook
      const result = await generateScript(textInput, 3); // 3 minutes duration
      
      if (result.success) {
        setTextInput(result.script);
        setSuccess('Script generated successfully and loaded into text area!');
        
        // Auto-dismiss success message
        setTimeout(() => setSuccess(null), 5000);
      } else {
        setError(result.error || 'Failed to generate script');
      }
    } catch (err) {
      console.error('❌ Error generating script:', err);
      setError('Failed to generate script. Please try again.');
    }
  };

  const handleGenerateAudio = async () => {
    if (!textInput.trim()) {
      setError('Please enter some text to convert to speech');
      return;
    }

    // Check if user has provided a voice sample (either uploaded or selected)
    if (voiceSelectionMode === 'upload' && !audioFile) {
      setError('Please upload an audio sample for voice cloning');
      return;
    }

    if (voiceSelectionMode === 'existing' && !selectedVoiceSample) {
      setError('Please select a voice sample from your existing assets');
      return;
    }

    setIsGeneratingAudio(true);
    setError(null);

    try {
      console.log('🎤 Creating TTS generation job...');
      
      let voiceAssetId;
      
      if (voiceSelectionMode === 'upload') {
        // Upload new audio file as an asset
        const formData = new FormData();
        formData.append('file', audioFile);
        formData.append('asset_type', 'voice_sample');
        formData.append('title', `Voice Sample - ${audioFile.name}`);
        formData.append('description', 'Voice sample for TTS generation');

        console.log('📤 Uploading voice sample asset...');
        const assetResponse = await assetService.uploadAsset(formData);
        
        if (!assetResponse.asset) {
          throw new Error('Failed to upload voice sample');
        }

        voiceAssetId = assetResponse.asset.id;
        console.log('✅ Voice sample uploaded:', voiceAssetId);
      } else {
        // Use existing selected voice sample
        voiceAssetId = selectedVoiceSample.id;
        console.log('✅ Using existing voice sample:', voiceAssetId);
      }
      
      // Create a job for TTS generation with the voice asset
      const jobData = {
        title: `TTS Generation - ${new Date().toLocaleString()}`,
        job_type: 'text_to_speech',
        description: `Text-to-speech generation for: "${textInput.substring(0, 50)}${textInput.length > 50 ? '...' : ''}"`,
        parameters: {
          text: textInput,
          voice_asset_id: voiceAssetId
        },
        priority: 'normal',
        asset_ids: [voiceAssetId]
      };

      console.log('🔄 Creating TTS job...');
      const response = await jobService.createJob(jobData);
      
      if (response.job) {
        setSuccess(`Audio generation job created successfully! Job ID: ${response.job.id}`);
        setTextInput('');
        
        // Clear the appropriate selection based on mode
        if (voiceSelectionMode === 'upload') {
          setAudioFile(null);
          setAudioPreview(null);
        } else {
          setSelectedVoiceSample(null);
        }
        
        // Auto-dismiss success message
        setTimeout(() => setSuccess(null), 5000);
        
        console.log('✅ TTS job created:', response.job.id);
      }
    } catch (err) {
      console.error('❌ Error creating TTS job:', err);
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError('Failed to create audio generation job. Please try again.');
      }
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  const handlePlayPreview = () => {
    if (audioRef.current) {
      if (isPlayingPreview) {
        audioRef.current.pause();
        setIsPlayingPreview(false);
      } else {
        audioRef.current.play();
        setIsPlayingPreview(true);
      }
    }
  };

  const handleAudioEnded = () => {
    setIsPlayingPreview(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Audio</h1>
        <p className="text-gray-600">
          Generate high-quality speech audio from text using voice cloning technology.
          Upload a voice sample and enter your text to create natural-sounding audio.
        </p>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Text Input Section */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <DocumentTextIcon className="h-6 w-6 text-blue-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Script Content</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="textInput" className="block text-sm font-medium text-gray-700 mb-2">
                Enter your text or script
              </label>
              <textarea
                id="textInput"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Enter the text you want to convert to speech, or use the AI generator below..."
                className="w-full h-40 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                disabled={isGeneratingScript}
              />
              <p className="text-sm text-gray-500 mt-1">
                {textInput.length} characters
              </p>
            </div>

            {/* AI Script Generation */}
            <div className="border-t pt-4">
              <div className="flex items-center mb-2">
                <SparklesIcon className="h-5 w-5 text-purple-600 mr-2" />
                <span className="text-sm font-medium text-gray-700">AI Script Generator</span>
              </div>
              <p className="text-sm text-gray-600 mb-3">
                Already have some text above? Click to expand it into a full script using AI.
              </p>
              <button
                onClick={handleGenerateScript}
                disabled={isGeneratingScript || !textInput.trim()}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingScript ? (
                  <>
                    <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="h-4 w-4 mr-2" />
                    Generate Full Script
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Voice Sample Section */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center mb-4">
            <MicrophoneIcon className="h-6 w-6 text-green-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-900">Voice Sample</h2>
          </div>

          {/* Voice Selection Mode Toggle */}
          <div className="mb-6">
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => handleVoiceSelectionModeChange('upload')}
                className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                  voiceSelectionMode === 'upload'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Upload New
              </button>
              <button
                onClick={() => handleVoiceSelectionModeChange('existing')}
                className={`flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors ${
                  voiceSelectionMode === 'existing'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Use Existing ({existingVoiceSamples.length})
              </button>
            </div>
          </div>

          {voiceSelectionMode === 'upload' ? (
            /* Upload Mode */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload audio sample for voice cloning
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
                  <div className="space-y-1 text-center">
                    {audioFile ? (
                      <div className="space-y-2">
                        <CloudArrowUpIcon className="mx-auto h-8 w-8 text-green-600" />
                        <div className="text-sm text-gray-900 font-medium">
                          {audioFile.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {(audioFile.size / (1024 * 1024)).toFixed(2)} MB
                        </div>
                        {audioPreview && (
                          <div className="flex items-center justify-center space-x-2">
                            <button
                              onClick={handlePlayPreview}
                              className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                            >
                              {isPlayingPreview ? (
                                <StopIcon className="h-3 w-3 mr-1" />
                              ) : (
                                <PlayIcon className="h-3 w-3 mr-1" />
                              )}
                              {isPlayingPreview ? 'Stop' : 'Preview'}
                            </button>
                            <audio
                              ref={audioRef}
                              src={audioPreview}
                              onEnded={handleAudioEnded}
                              className="hidden"
                            />
                          </div>
                        )}
                      </div>
                    ) : (
                      <>
                        <MicrophoneIcon className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="text-sm text-gray-600">
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="font-medium text-blue-600 hover:text-blue-500"
                          >
                            Upload an audio file
                          </button>
                          <p className="text-xs text-gray-500 mt-1">
                            WAV, MP3, or OGG up to 10MB
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>

              {audioFile && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <MicrophoneIcon className="h-5 w-5 text-blue-400" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-blue-800">
                        Voice sample ready
                      </h3>
                      <div className="text-sm text-blue-700 mt-1">
                        This audio will be used to clone the voice for your generated speech.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* Existing Voice Samples Mode */
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select from your existing voice samples
                </label>
                
                {loadingVoiceSamples ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin h-6 w-6 border-2 border-gray-300 border-t-green-600 rounded-full"></div>
                    <span className="ml-2 text-sm text-gray-600">Loading voice samples...</span>
                  </div>
                ) : existingVoiceSamples.length === 0 ? (
                  <div className="text-center py-8 border-2 border-gray-200 border-dashed rounded-lg">
                    <MicrophoneIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No voice samples yet</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Upload your first voice sample using the "Upload New" tab.
                    </p>
                  </div>
                ) : (
                  <div className="grid gap-3 max-h-64 overflow-y-auto">
                    {existingVoiceSamples.map((sample) => (
                      <div
                        key={sample.id}
                        onClick={() => handleVoiceSampleSelect(sample)}
                        className={`relative border rounded-lg p-3 cursor-pointer transition-colors ${
                          selectedVoiceSample?.id === sample.id
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="flex-shrink-0">
                              <MicrophoneIcon className={`h-5 w-5 ${
                                selectedVoiceSample?.id === sample.id ? 'text-green-600' : 'text-gray-400'
                              }`} />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {sample.filename}
                              </p>
                              <p className="text-xs text-gray-500">
                                {sample.file_size ? `${(sample.file_size / (1024 * 1024)).toFixed(2)} MB` : 'Unknown size'} • 
                                {' '}Uploaded {new Date(sample.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                          {selectedVoiceSample?.id === sample.id && (
                            <div className="flex-shrink-0">
                              <CheckCircleIcon className="h-5 w-5 text-green-600" />
                            </div>
                          )}
                        </div>
                        
                        {sample.download_url && (
                          <div className="mt-2">
                            <audio
                              controls
                              className="w-full h-8"
                              style={{ height: '32px' }}
                            >
                              <source src={sample.download_url} type={sample.mime_type || 'audio/wav'} />
                              Your browser does not support the audio element.
                            </audio>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedVoiceSample && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <CheckCircleIcon className="h-5 w-5 text-green-400" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-green-800">
                        Voice sample selected
                      </h3>
                      <div className="text-sm text-green-700 mt-1">
                        "{selectedVoiceSample.filename}" will be used to clone the voice for your generated speech.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Generate Audio Button */}
      <div className="mt-8 flex justify-center">
        <button
          onClick={handleGenerateAudio}
          disabled={isGeneratingAudio || !textInput.trim() || (voiceSelectionMode === 'upload' && !audioFile) || (voiceSelectionMode === 'existing' && !selectedVoiceSample)}
          className="inline-flex items-center px-8 py-4 border border-transparent text-lg font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
        >
          {isGeneratingAudio ? (
            <>
              <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
              Creating Audio...
            </>
          ) : (
            <>
              <MicrophoneIcon className="h-5 w-5 mr-3" />
              Generate Audio
            </>
          )}
        </button>
      </div>

      {/* Instructions */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-3">How it works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">1</span>
            <div>
              <strong>Enter Text:</strong> Type your script or use the AI generator to create content from a topic or prompt.
            </div>
          </div>
          <div className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">2</span>
            <div>
              <strong>Upload Sample:</strong> Provide a clear audio sample of the voice you want to clone (10-30 seconds recommended).
            </div>
          </div>
          <div className="flex items-start">
            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">3</span>
            <div>
              <strong>Generate:</strong> Click generate to create high-quality speech audio that matches the provided voice sample.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateAudioPage;
