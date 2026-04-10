import { createRouter, createWebHashHistory } from "vue-router"
import { isAuthenticated } from "./stores/auth"

const routes = [
  { path: "/login", name: "Login", component: () => import("./views/LoginView.vue") },
  { path: "/", name: "Pipeline", component: () => import("./views/PipelineView.vue"), meta: { requiresAuth: true } },
  { path: "/editor", name: "Editor", component: () => import("./views/EditorView.vue"), meta: { requiresAuth: true } },
  { path: "/analytics/:id?", name: "Analytics", component: () => import("./views/AnalyticsView.vue"), meta: { requiresAuth: true } },
  { path: "/fingerprint", name: "Fingerprint", component: () => import("./views/FingerprintView.vue"), meta: { requiresAuth: true } },
  { path: "/settings", name: "Settings", component: () => import("./views/SettingsView.vue"), meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  return true
})

export default router
