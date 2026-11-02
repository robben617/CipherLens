import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/workbench', name: 'workbench', component: () => import('../views/WorkbenchView.vue') },
  { path: '/sbox', name: 'sbox', component: () => import('../views/SBoxView.vue') },
  { path: '/practice', name: 'practice', component: () => import('../views/PracticeView.vue') },
  { path: '/records', name: 'records', component: () => import('../views/RecordsView.vue') },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})