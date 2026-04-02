import { createApp } from 'vue'
import axios from 'axios'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import router from './router'

axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'https://ai-screenplay-system.onrender.com/api' : '/api')

if (import.meta.env.PROD) {
  axios.get('/health', { timeout: 8000 }).catch(() => {})
}

const app = createApp(App)
app.use(ElementPlus)
app.use(createPinia())
app.use(router)
app.mount('#app')