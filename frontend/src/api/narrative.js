import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const syncNarrativeGraph = async (content) => {
  return await apiClient.post('/narrative/sync_graph', { content })
}

export const generateNextBeat = async (content, outline = '', characters = '') => {
  return await apiClient.post('/narrative/generate_beat', {
    content,
    outline,
    characters,
  })
}

export const checkScriptCompletion = async (content, outline = '') => {
  return await apiClient.post('/narrative/check_completion', {
    content,
    outline,
  })
}
