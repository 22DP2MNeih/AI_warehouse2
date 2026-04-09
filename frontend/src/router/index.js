import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue'),
    },
    {
      path: '/warehouse',
      name: 'warehouse',
      component: () => import('../views/WarehouseView.vue'),
    },
    {
      path: '/company',
      name: 'company',
      component: () => import('../views/CompanyView.vue'),
    },
    {
      path: '/parts',
      name: 'parts',
      component: () => import('../views/PartListingView.vue'),
    },
    {
      path: '/orders',
      name: 'orders',
      component: () => import('../views/OrdersView.vue'),
    },
    {
      path: '/ai_predictions',
      name: 'ai_predictions',
      component: () => import('../views/AIPredictionView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
  ],
})

export default router
