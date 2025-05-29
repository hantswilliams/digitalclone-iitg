import React, { useState, useEffect, useCallback } from 'react';
import { assetService } from '../services/assetService';
import { jobService } from '../services/jobService';
import { ChevronLeftIcon, ChevronRightIcon, PlayIcon } from '@heroicons/react/24/outline';

const WizardSteps = ({ currentStep, steps }) => {
  return (
    <div className="flex items-center justify-center space-x-4 mb-8">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
            index < currentStep 
              ? 'bg-green-500 text-white' 
              : index === currentStep 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-500'
          }`}>
            {index < currentStep ? '✓' : index + 1}
          </div>
          <span className={`ml-2 text-sm font-medium ${
            index <= currentStep ? 'text-gray-900' : 'text-gray-400'
          }`}>
            {step.title}
          </span>
          {index < steps.length - 1 && (
            <ChevronRightIcon className="h-4 w-4 text-gray-400 ml-4" />
          )}
        </div>
      ))}
    </div>
  );
};

const AssetSelector = ({ assetType, selectedAsset, onSelect, label, description }) => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [playingAudio, setPlayingAudio] = useState(null);

  const loadAssets = useCallback(async () => {
    try {
      const response = await assetService.getAssets({ type: assetType, status: 'ready' });
      setAssets(response.assets || []);
    } catch (err) {
      console.error('Error loading assets:', err);
    } finally {
      setLoading(false);
    }
  }, [assetType]);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  const getAssetIcon = (type) => {
    switch (type) {
      case 'portrait': return '🖼️';
      case 'voice_sample': return '🎵';
      case 'script': return '📄';
      default: return '📁';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const playVoiceSample = (e, asset) => {
    e.stopPropagation(); // Prevent selecting the asset
    
    if (playingAudio) {
      playingAudio.pause();
      setPlayingAudio(null);
    }

    const audio = new Audio(asset.download_url);
    audio.onended = () => setPlayingAudio(null);
    audio.play();
    setPlayingAudio(audio);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-gray-900">{label}</h3>
        <div className="animate-pulse space-y-2">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900">{label}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>

      {assets.length === 0 ? (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <div className="text-2xl mb-2">{getAssetIcon(assetType)}</div>
          <p className="text-gray-500">No {assetType} assets available</p>
          <a
            href="/assets"
            className="text-blue-600 hover:text-blue-500 text-sm font-medium mt-2 inline-block"
          >
            Upload {assetType} asset →
          </a>
        </div>
      ) : (
        <div className="space-y-2">
          {assets.map((asset) => (
            <div
              key={asset.id}
              onClick={() => onSelect(asset)}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedAsset?.id === asset.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-3">
                {assetType === 'portrait' && asset.download_url ? (
                  <img
                    src={asset.download_url}
                    alt={asset.filename}
                    className="w-12 h-12 object-cover rounded-lg border border-gray-200"
                  />
                ) : (
                  <div className="text-xl">{getAssetIcon(asset.asset_type)}</div>
                )}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{asset.filename}</h4>
                  <p className="text-sm text-gray-500">
                    Uploaded: {new Date(asset.created_at).toLocaleDateString()}
                    {asset.file_size && ` • ${formatFileSize(asset.file_size)}`}
                  </p>
                  {asset.description && (
                    <p className="text-sm text-gray-600 mt-1">{asset.description}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {assetType === 'voice_sample' && asset.download_url && (
                    <button
                      onClick={(e) => playVoiceSample(e, asset)}
                      className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                      title="Preview audio"
                    >
                      <PlayIcon className="h-4 w-4" />
                    </button>
                  )}
                  {selectedAsset?.id === asset.id && (
                    <div className="text-blue-500 text-xl">✓</div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ScriptInput = ({ script, onScriptChange, selectedVoice }) => {
  const [scriptAssets, setScriptAssets] = useState([]);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [inputMode, setInputMode] = useState('write'); // 'write' or 'select'

  // Load existing script assets
  useEffect(() => {
    const loadScriptAssets = async () => {
      try {
        setLoadingAssets(true);
        const response = await assetService.getAssets({ type: 'script', status: 'ready' });
        setScriptAssets(response.assets || []);
      } catch (err) {
        console.error('Error loading script assets:', err);
      } finally {
        setLoadingAssets(false);
      }
    };

    loadScriptAssets();
  }, []);

  const loadScriptContent = async (asset) => {
    try {
      const response = await fetch(asset.download_url);
      if (!response.ok) {
        throw new Error('Failed to fetch script content');
      }
      const text = await response.text();
      onScriptChange(text);
      setInputMode('write'); // Switch to write mode after loading
    } catch (err) {
      console.error('Error loading script content:', err);
      alert('Failed to load script content');
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Script</h3>
        <p className="text-sm text-gray-600">Choose an existing script or write a new one</p>
      </div>

      {/* Mode Selector */}
      <div className="flex space-x-4 border-b border-gray-200">
        <button
          onClick={() => setInputMode('write')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 ${
            inputMode === 'write'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Write New Script
        </button>
        <button
          onClick={() => setInputMode('select')}
          className={`pb-2 px-1 text-sm font-medium border-b-2 ${
            inputMode === 'select'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Use Existing Script ({scriptAssets.length})
        </button>
      </div>

      {inputMode === 'select' && (
        <div className="space-y-2">
          {loadingAssets ? (
            <div className="animate-pulse space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded"></div>
              ))}
            </div>
          ) : scriptAssets.length === 0 ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <div className="text-2xl mb-2">📄</div>
              <p className="text-gray-500">No script assets available</p>
              <a
                href="/assets"
                className="text-blue-600 hover:text-blue-500 text-sm font-medium mt-2 inline-block"
              >
                Upload script file →
              </a>
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {scriptAssets.map((asset) => (
                <div
                  key={asset.id}
                  onClick={() => loadScriptContent(asset)}
                  className="p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="text-xl">📄</div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{asset.filename}</h4>
                      <p className="text-sm text-gray-500">
                        Uploaded: {new Date(asset.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-blue-600 text-sm font-medium">Load Script</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {inputMode === 'write' && (
        <>
          <textarea
            value={script}
            onChange={(e) => onScriptChange(e.target.value)}
            placeholder="Enter your script here..."
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {script.length} characters • ~{Math.ceil(script.length / 150)} seconds
            </div>
          </div>
        </>
      )}
    </div>
  );
};

const ReviewStep = ({ portrait, voice, script, onGenerate, isGenerating }) => {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Review Your Video</h3>
        <p className="text-sm text-gray-600">Review your selections before generating the video</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Portrait</h4>
          {portrait ? (
            <div>
              <div className="text-2xl mb-2">🖼️</div>
              <p className="text-sm text-gray-700">{portrait.filename}</p>
            </div>
          ) : (
            <p className="text-red-500 text-sm">No portrait selected</p>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Voice</h4>
          {voice ? (
            <div>
              <div className="text-2xl mb-2">🎵</div>
              <p className="text-sm text-gray-700">{voice.filename}</p>
            </div>
          ) : (
            <p className="text-red-500 text-sm">No voice selected</p>
          )}
        </div>

        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Script</h4>
          <p className="text-sm text-gray-700">
            {script ? `${script.length} characters` : 'No script entered'}
          </p>
        </div>
      </div>

      {script && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Script Preview</h4>
          <p className="text-sm text-gray-700 italic">"{script.substring(0, 200)}..."</p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Estimated Generation Time</h4>
        <p className="text-sm text-blue-700">
          This video will take approximately 2-5 minutes to generate depending on script length.
        </p>
      </div>

      <button
        onClick={() => {
          console.log('🔘 Generate Video button clicked');
          console.log('📍 Button state:', { 
            isGenerating, 
            hasPortrait: !!portrait, 
            hasVoice: !!voice, 
            hasScript: !!script,
            onGenerate: typeof onGenerate 
          });
          if (onGenerate) {
            onGenerate();
          } else {
            console.error('❌ onGenerate is not defined!');
          }
        }}
        disabled={isGenerating || !portrait || !voice || !script}
        className="w-full px-4 py-3 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? 'Generating Video...' : 'Generate Video'}
      </button>
    </div>
  );
};

const CreateVideoPage = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedPortrait, setSelectedPortrait] = useState(null);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [script, setScript] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedJob, setGeneratedJob] = useState(null);

  const steps = [
    { id: 'portrait', title: 'Select Portrait' },
    { id: 'voice', title: 'Select Voice' },
    { id: 'script', title: 'Write Script' },
    { id: 'review', title: 'Review & Generate' }
  ];

  const canProceed = () => {
    switch (currentStep) {
      case 0: return selectedPortrait;
      case 1: return selectedVoice;
      case 2: return script.trim().length > 0;
      case 3: return true;
      default: return false;
    }
  };

  const handleNext = () => {
    if (canProceed() && currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGenerate = async () => {
    console.log('🎬 ================== STARTING VIDEO GENERATION ==================');
    console.log('🎬 handleGenerate called at:', new Date().toISOString());
    console.log('📋 Current state:', {
      selectedPortrait: selectedPortrait?.id,
      selectedPortraitName: selectedPortrait?.name,
      selectedPortraitType: selectedPortrait?.type,
      selectedVoice: selectedVoice?.id,
      selectedVoiceName: selectedVoice?.name,
      selectedVoiceType: selectedVoice?.type,
      scriptLength: script?.length,
      scriptPreview: script?.substring(0, 100) + (script?.length > 100 ? '...' : ''),
      isGenerating
    });

    // Validation checks with detailed logging
    if (!selectedPortrait) {
      console.error('❌ VALIDATION FAILED: No portrait selected');
      alert('Please select a portrait image before generating video.');
      return;
    }
    
    if (!selectedVoice) {
      console.error('❌ VALIDATION FAILED: No voice selected');
      alert('Please select a voice before generating video.');
      return;
    }
    
    if (!script || script.trim().length === 0) {
      console.error('❌ VALIDATION FAILED: No script provided');
      alert('Please provide a script before generating video.');
      return;
    }

    console.log('✅ VALIDATION PASSED: All required fields present');

    try {
      setIsGenerating(true);
      console.log('⏳ Setting isGenerating to true');
      
      const jobData = {
        title: 'Video Generation',
        description: 'Video generation from create wizard',
        job_type: 'full_pipeline',
        priority: 'normal',
        parameters: {
          portrait_asset_id: selectedPortrait.id,
          voice_asset_id: selectedVoice.id,
          script: script,
          output_format: 'mp4',
          // Additional debug info
          frontend_timestamp: new Date().toISOString(),
          frontend_version: 'create-video-wizard-v1'
        },
        asset_ids: [selectedPortrait.id, selectedVoice.id]
      };

      console.log('📤 SENDING JOB DATA:', JSON.stringify(jobData, null, 2));
      console.log('🔗 Calling jobService.createJob...');
      
      const startTime = Date.now();
      const response = await jobService.createJob(jobData);
      const requestDuration = Date.now() - startTime;
      
      console.log('✅ JOB CREATION RESPONSE RECEIVED:', {
        duration: `${requestDuration}ms`,
        response: response,
        responseData: response.data,
        responseKeys: Object.keys(response),
        hasJobData: !!response.data?.job || !!response.job
      });
      
      const jobResult = response.data || response;
      setGeneratedJob(jobResult);
      console.log('🎯 Setting generatedJob:', jobResult);
      console.log('🆔 Job ID:', jobResult?.job?.id || jobResult?.id);
      console.log('📊 Job Status:', jobResult?.job?.status || jobResult?.status);
      console.log('🎬 ================== VIDEO GENERATION INITIATED ==================');
      
    } catch (err) {
      console.error('❌ ================== VIDEO GENERATION FAILED ==================');
      console.error('❌ Error generating video:', err);
      console.error('📊 Error details:', {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        stack: err.stack,
        config: err.config ? {
          url: err.config.url,
          method: err.config.method,
          headers: err.config.headers
        } : null
      });
      
      // More descriptive error messages
      let errorMessage = 'Failed to start video generation. ';
      if (err.response?.status === 401) {
        errorMessage += 'Authentication failed. Please log in again.';
      } else if (err.response?.status === 400) {
        errorMessage += 'Invalid request data. Please check your inputs.';
      } else if (err.response?.status === 500) {
        errorMessage += 'Server error. Please try again later.';
      } else if (err.message.includes('Network Error')) {
        errorMessage += 'Network connection failed. Please check your internet connection.';
      } else {
        errorMessage += 'Please try again.';
      }
      
      alert(errorMessage);
      console.error('🎬 ================== END ERROR LOG ==================');
    } finally {
      setIsGenerating(false);
      console.log('🔄 Setting isGenerating to false');
      console.log('🎬 ================== VIDEO GENERATION PROCESS ENDED ==================');
    }
  };

  if (generatedJob) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🎬</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Video Generation Started!</h1>
          <p className="text-gray-600 mb-6">
            Your video is being generated. You can monitor the progress on the Jobs page.
          </p>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800 font-medium">Job ID: {generatedJob.job?.id || generatedJob.id}</p>
            <p className="text-green-700 text-sm">Status: {generatedJob.job?.status || generatedJob.status}</p>
          </div>

          <div className="space-x-4">
            <a
              href="/jobs"
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              View Jobs
            </a>
            <button
              onClick={() => {
                setGeneratedJob(null);
                setCurrentStep(0);
                setSelectedPortrait(null);
                setSelectedVoice(null);
                setScript('');
              }}
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              Create Another Video
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Create Video</h1>
        <p className="text-gray-600">Generate a talking-head video with your digital avatar</p>
      </div>

      <WizardSteps currentStep={currentStep} steps={steps} />

      <div className="bg-white rounded-lg shadow border border-gray-200 p-6 min-h-96">
        {currentStep === 0 && (
          <AssetSelector
            assetType="portrait"
            selectedAsset={selectedPortrait}
            onSelect={setSelectedPortrait}
            label="Select Portrait"
            description="Choose a portrait photo that will be used for your digital avatar"
          />
        )}

        {currentStep === 1 && (
          <AssetSelector
            assetType="voice_sample"
            selectedAsset={selectedVoice}
            onSelect={setSelectedVoice}
            label="Select Voice"
            description="Choose a voice sample that will be cloned for your avatar"
          />
        )}

        {currentStep === 2 && (
          <ScriptInput
            script={script}
            onScriptChange={setScript}
            selectedVoice={selectedVoice}
          />
        )}

        {currentStep === 3 && (
          <>
            {console.log('📍 Rendering ReviewStep:', {
              currentStep,
              selectedPortrait: selectedPortrait?.id,
              selectedVoice: selectedVoice?.id,
              scriptLength: script?.length,
              handleGenerate: typeof handleGenerate
            })}
            <ReviewStep
              portrait={selectedPortrait}
              voice={selectedVoice}
              script={script}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />
          </>
        )}
      </div>

      <div className="flex justify-between mt-6">
        <button
          onClick={handlePrevious}
          disabled={currentStep === 0}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <ChevronLeftIcon className="h-4 w-4 mr-1" />
          Previous
        </button>

        {currentStep < steps.length - 1 ? (
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRightIcon className="h-4 w-4 ml-1" />
          </button>
        ) : (
          <div className="w-20"></div> // Spacer to maintain layout
        )}
      </div>
    </div>
  );
};

export default CreateVideoPage;
