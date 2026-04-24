import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  // baseURL: 'http://localhost:8000/api',
  // baseURL: 'http://localhost:5173/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor (optional: handle 401)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && error.response.status === 401) {
      if (!error.config.url.includes('auth/token')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default {
  // Global Products
  getProducts() {
    return apiClient.get('/products/');
  },

  // Company Catalog (SKU, Price)
  getCompanyProducts() {
    return apiClient.get('/company-products/');
  },

  // Physical Warehouse Stock (The main "Inventory" view)
  getInventory() {
    return apiClient.get('/stock/');
  },
  getStockItem(id) {
    return apiClient.get(`/stock/${id}/`);
  },
  updateStock(id, data) {
    return apiClient.put(`/stock/${id}/`, data);
  },
  deleteStock(id) {
    return apiClient.delete(`/stock/${id}/`);
  },

  // Backward compatibility alias for PartFormView
  getPart(id) {
    return this.getStockItem(id);
  },
  createPart(data) {
    return apiClient.post('/stock/', data);
  },
  updatePart(id, data) {
    return this.updateStock(id, data);
  },
  deletePart(id) {
    return this.deleteStock(id);
  },

  // Auth
  login(credentials) {
    return apiClient.post('/auth/token/', credentials);
  },
  register(userData) {
    return apiClient.post('/auth/register/', userData);
  },

  // Orders
  createOrder(order) {
    return apiClient.post('/orders/', order);
  },
  getOrders() {
    return apiClient.get('/orders/');
  },
  approveOrder(id) {
    return apiClient.post(`/orders/${id}/approve/`);
  },
  rejectOrder(id) {
    return apiClient.post(`/orders/${id}/reject/`);
  },
  completeOrder(id) {
    return apiClient.post(`/orders/${id}/complete/`);
  },
  deleteOrder(id) {
    return apiClient.delete(`/orders/${id}/`);
  },

  // Market
  getMarket() {
    return apiClient.get('/market/');
  },
  getMarketAvailability(id) {
    return apiClient.get(`/market/${id}/availability/`);
  },

  // Warehouses
  getWarehouses() {
    return apiClient.get('/warehouses/');
  },

  // CEO / Management
  getCompanyUsers() {
    return apiClient.get('/auth/users/');
  },
  updateUserRole(id, role) {
    return apiClient.patch(`/auth/users/${id}/`, { role });
  },
  deleteUser(id) {
    return apiClient.delete(`/auth/users/${id}/`);
  },

  // Import/Export
  exportOrdersCsv() {
    return apiClient.get('/orders/export_csv/', { responseType: 'blob' });
  },
  bulkCompleteOrders() {
    return apiClient.post('/orders/bulk_complete/');
  },
  importOrdersCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/orders/import_csv/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportPartsCsv() {
    return apiClient.get('/stock/export_csv/', { responseType: 'blob' });
  },
  importPartsCsv(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/stock/import_csv/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // AI Management
  getCompanySettings() {
    return apiClient.get('/company-settings/');
  },
  updateCompanySettings(companyId, data) {
    return apiClient.patch(`/company-settings/${companyId}/`, data);
  },
  getAIRecommendations() {
    return apiClient.get('/stock/ai_recommendations/');
  },
  trainAI(companyId) {
    return apiClient.post(`/company-settings/${companyId}/train/`);
  },
  trainAllCompanies() {
    return apiClient.post('/company-settings/train_all/');
  }
};
