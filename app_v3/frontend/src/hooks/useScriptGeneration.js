import { useState, useCallback } from 'react';
import { jobService } from '../services/jobService';
import { assetService } from '../services/assetService';

export const useScriptGeneration = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState(null);

  const pollForCompletion = useCallback(async (jobId, maxAttempts = 150, interval = 2000) => {
    console.log(`🔄 Starting to poll job ${jobId} for completion...`);
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        console.log(`📊 Polling attempt ${attempt}/${maxAttempts} for job ${jobId}`);
        const jobResponse = await jobService.getJob(jobId);
        
        // Handle the API response structure: {job: {...}} or directly {...}
        const jobStatus = jobResponse.job || jobResponse;
        
        console.log(`📈 Job ${jobId} status:`, jobStatus.status);
        
        if (jobStatus.status === 'completed') {
          console.log('✅ Job completed successfully!');
          
          // Fetch the generated script content from assets
          if (jobStatus.asset_ids && jobStatus.asset_ids.length > 0) {
            console.log('📄 Fetching assets from asset_ids:', jobStatus.asset_ids);
            
            try {
              // Fetch all assets for this job
              const assetPromises = jobStatus.asset_ids.map(async (assetId) => {
                try {
                  const asset = await assetService.getAsset(assetId);
                  return { id: assetId, data: asset };
                } catch (error) {
                  console.warn(`⚠️ Could not load asset ${assetId}:`, error);
                  return { id: assetId, data: null };
                }
              });

              const assetResults = await Promise.all(assetPromises);
              
              // Find the script asset
              const scriptAssetResult = assetResults.find(({ data }) => 
                data && data.asset_type === 'script'
              );
              
              if (scriptAssetResult && scriptAssetResult.data) {
                const scriptAsset = scriptAssetResult.data;
                
                if (scriptAsset.status === 'ready' && scriptAsset.download_url) {
                  console.log('📄 Fetching script content from:', scriptAsset.download_url);
                  
                  const response = await fetch(scriptAsset.download_url);
                  if (!response.ok) {
                    throw new Error(`Failed to fetch script: ${response.status} ${response.statusText}`);
                  }
                  const scriptContent = await response.text();
                  console.log('✅ Script content fetched successfully:', scriptContent.substring(0, 100) + '...');
                  return { success: true, script: scriptContent };
                } else {
                  console.error('❌ Script asset not ready or missing download URL:', scriptAsset);
                  return { success: false, error: 'Script asset is not ready for download' };
                }
              } else {
                console.error('❌ No script asset found in job assets');
                return { success: false, error: 'No script content found in job output' };
              }
            } catch (fetchError) {
              console.error('❌ Failed to fetch assets:', fetchError);
              return { success: false, error: 'Failed to fetch generated script assets' };
            }
          } else {
            console.error('❌ No asset_ids found in job');
            return { success: false, error: 'No assets generated' };
          }
        } else if (jobStatus.status === 'failed') {
          console.error('❌ Job failed:', jobStatus.error_message);
          return { success: false, error: jobStatus.error_message || 'Job failed' };
        } else if (jobStatus.status === 'cancelled') {
          console.log('⚠️ Job was cancelled');
          return { success: false, error: 'Job was cancelled' };
        }
        
        // Wait before next poll
        if (attempt < maxAttempts) {
          console.log(`⏳ Waiting ${interval}ms before next poll...`);
          await new Promise(resolve => setTimeout(resolve, interval));
        }
      } catch (error) {
        console.error(`❌ Error polling job ${jobId} (attempt ${attempt}):`, error);
        
        // If it's a 404, the job doesn't exist
        if (error.response?.status === 404) {
          return { success: false, error: 'Job not found' };
        }
        
        // For other errors, continue polling unless it's the last attempt
        if (attempt === maxAttempts) {
          return { success: false, error: 'Polling timeout - job status unknown' };
        }
        
        // Wait before next poll
        console.log(`⏳ Waiting ${interval}ms before retry...`);
        await new Promise(resolve => setTimeout(resolve, interval));
      }
    }
    
    return { success: false, error: 'Polling timeout' };
  }, []);

  const generateScript = useCallback(async (prompt, durationMinutes = 3) => {
    setIsGenerating(true);
    setGenerationError(null);

    try {
      console.log('🤖 Starting LLM script generation...', { prompt, durationMinutes });
      
      // Start script generation job
      const response = await jobService.createJob({
        title: `Script Generation - ${prompt.substring(0, 50)}...`,
        job_type: 'script_generation',
        description: `Generated script for: ${prompt.substring(0, 100)}...`,
        priority: 'normal',
        parameters: {
          prompt: prompt,
          duration_minutes: durationMinutes,
          max_tokens: 512,
          temperature: 0.7
        }
      });

      console.log('✅ LLM generation job created:', response);
      const jobId = response.job?.id || response.id;

      if (!jobId) {
        throw new Error('No job ID received from server');
      }

      // Poll for completion
      const pollResult = await pollForCompletion(jobId);
      
      if (pollResult.success) {
        console.log('✅ Script generation completed successfully');
        return {
          success: true,
          script: pollResult.script,
          jobId: jobId
        };
      } else {
        throw new Error(pollResult.error || 'Script generation failed');
      }
    } catch (error) {
      console.error('❌ Script generation failed:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Failed to generate script';
      setGenerationError(errorMessage);
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      setIsGenerating(false);
    }
  }, [pollForCompletion]);

  const clearError = useCallback(() => {
    setGenerationError(null);
  }, []);

  return {
    generateScript,
    isGenerating,
    generationError,
    clearError
  };
};
