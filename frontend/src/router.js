import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", name: "Pipeline", component: () => import("./views/PipelineView.vue") },
  { path: "/editor", name: "Editor", component: () => import("./views/EditorView.vue") },
  { path: "/analytics/:id?", name: "Analytics", component: () => import("./views/AnalyticsView.vue") },
  { path: "/fingerprint", name: "Fingerprint", component: () => import("./views/FingerprintView.vue") },
  { path: "/settings", name: "Settings", component: () => import("./views/SettingsView.vue") }
]

const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes })
export default router
