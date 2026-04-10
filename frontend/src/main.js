import { createApp } from 'vue'
import axios from 'axios'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import router from './router'

const RUNTIME_API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const API_HOST_BASE = RUNTIME_API_BASE.replace(/\/api\/?$/, '')
const LOCAL_RUNTIME_HEARTBEAT_KEY = 'LOCAL_APP_RUNTIME_CLIENT_ID'
const LOCAL_RUNTIME_HEARTBEAT_URL = `${RUNTIME_API_BASE}/runtime/heartbeat`
const LOCAL_RUNTIME_RELEASE_URL = `${RUNTIME_API_BASE}/runtime/release`

axios.defaults.baseURL = API_HOST_BASE

if (import.meta.env.PROD) {
  axios.get('/health', { timeout: 8000 }).catch(() => {})
}

function createRuntimeClientId() {
  return window.crypto?.randomUUID?.() || `local-app-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function setupLocalRuntimeHeartbeat() {
  const isLocalHost = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
  if (!import.meta.env.PROD || !isLocalHost) return

  let clientId = sessionStorage.getItem(LOCAL_RUNTIME_HEARTBEAT_KEY)
  if (!clientId) {
    clientId = createRuntimeClientId()
    sessionStorage.setItem(LOCAL_RUNTIME_HEARTBEAT_KEY, clientId)
  }

  const payload = JSON.stringify({ client_id: clientId })

  const postJson = (url, body, keepalive = false) =>
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      keepalive,
    }).catch(() => {})

  const sendHeartbeat = () => postJson(LOCAL_RUNTIME_HEARTBEAT_URL, payload)

  const releaseRuntime = () => {
    if (navigator.sendBeacon) {
      try {
        const blob = new Blob([payload], { type: 'application/json' })
        navigator.sendBeacon(LOCAL_RUNTIME_RELEASE_URL, blob)
        return
      } catch {
      }
    }

    postJson(LOCAL_RUNTIME_RELEASE_URL, payload, true)
  }

  sendHeartbeat()
  window.setInterval(sendHeartbeat, 5000)
  window.addEventListener('pageshow', sendHeartbeat)
  window.addEventListener('pagehide', releaseRuntime)
  window.addEventListener('beforeunload', releaseRuntime)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      sendHeartbeat()
    }
  })
}

setupLocalRuntimeHeartbeat()

const app = createApp(App)
app.use(ElementPlus)
app.use(createPinia())
app.use(router)
app.mount('#app')
