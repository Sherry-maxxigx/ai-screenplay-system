
import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Generate Character Profiles
export const generateCharacters = async (idea) => {
  return await apiClient.post('/ai/narrative/characters', { idea })
}

// Generate Outline
export const generateOutline = async (idea, characters) => {
  return await apiClient.post('/ai/narrative/outline', { idea, characters })
}

// Generate Script
export const generatePipelineScript = async (idea, characters, outline) => {
  return await apiClient.post('/ai/narrative/script', { idea, characters, outline })
}

export const getRuntimeAISettings = async () => {
  return await apiClient.get('/ai/runtime-settings')
}

export const saveRuntimeAISettings = async (payload) => {
  return await apiClient.post('/ai/runtime-settings', payload)
}
