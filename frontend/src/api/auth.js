import axios from 'axios'

// 开发环境: 如果设置了VITE_API_BASE_URL则使用，否则使用/api（由Vite代理处理）
// 生产环境: 使用/api（后端直接提供API）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const authClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

export const loginAPI = async (payload) => authClient.post('/auth/login', payload)

export const registerAPI = async (payload) => authClient.post('/auth/register', payload)
