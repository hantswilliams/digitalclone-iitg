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

  // Generate video
  generateVideo: async (videoData) => {
    const response = await api.post('/api/generate/video', videoData);
    return response.data;
  },

  // Validate TTS service
  validateTTS: async () => {
    const response = await api.get('/api/generate/tts/validate');
    return response.data;
  },

  // Validate video generation service
  validateVideo: async () => {
    const response = await api.get('/api/generate/video/validate');
    return response.data;
  },

  // Validate LLM service
  validateLLM: async () => {
    const response = await api.get('/api/generate/llm/validate');
    return response.data;
  },
};
