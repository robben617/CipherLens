import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const routes: RouteRecordRaw[] = [
  { path: '/', name: 'home', component: HomeView, meta: { title: '看得见的 AES' } },
  {
    path: '/workbench',
    name: 'workbench',
    component: () => import('../views/WorkbenchView.vue'),
    meta: { title: '工作台', bare: true },
  },
  { path: '/sbox', name: 'sbox', component: () => import('../views/SBoxView.vue'), meta: { title: 'S 盒' } },
{
    path: '/avalanche',
    name: 'avalanche',
    component: () => import('../views/AvalancheView.vue'),
    meta: { title: '雪崩实验' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.afterEach((to) => {
  const title = typeof to.meta.title === 'string' ? to.meta.title : ''
  document.title = title ? `${title} · CipherLens` : 'CipherLens · 密码透镜'
})
