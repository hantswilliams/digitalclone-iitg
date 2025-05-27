import api from './api';

export const generationService = {
  // Generate script using LLM
  generateScript: async (scriptData) => {
    const response = await api.post('/api/generate/script', scriptData);
    return response.data;
  },

  // Generate audio using TTS
  generateTTS: async (ttsData) => {
    const response = await api.post('/api/generate/tts', ttsData);
    return response.data;
  },

  // Generate text-to-speech (alias for generateTTS)
  generateTextToSpeech: async (ttsData) => {
    const response = await api.post('/api/generate/text-to-speech', ttsData);
    return response.data;
  },

  // Generate video
  generateVideo: async (videoData) => {
    const response = await api.post('/api/generate/video', videoData);
    return response.data;
  },

  // Check TTS service status
  getTTSStatus: async () => {
    const response = await api.get('/api/generate/tts/status');
    return response.data;
  },

  // Check video generation service status
  getVideoStatus: async () => {
    const response = await api.get('/api/generate/video/status');
    return response.data;
  },

  // Check LLM service status
  getLLMStatus: async () => {
    const response = await api.get('/api/generate/llm/status');
    return response.data;
  },

  // Check worker status (using ping endpoint which doesn't require auth)
  getWorkerStatus: async () => {
    const response = await api.get('/api/worker/ping');
    return response.data;
  },

  // Validate TTS service (deprecated - use getTTSStatus)
  validateTTS: async () => {
    const response = await api.get('/api/generate/tts/status');
    return response.data;
  },

  // Validate video generation service (deprecated - use getVideoStatus)
  validateVideo: async () => {
    const response = await api.get('/api/generate/video/status');
    return response.data;
  },

  // Validate LLM service (deprecated - use getLLMStatus)
  validateLLM: async () => {
    const response = await api.get('/api/generate/llm/status');
    return response.data;
  },
};
