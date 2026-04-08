<script setup>
import { ref, computed } from 'vue';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';

// --- 1. AI Configuration & Filters ---
const filters = ref({
  search: '',
  serviceLevel: 95,
  weighting: 'Exponential',
  priority: 'Cost-Optimized',
  thresholdTime: 30, // Days
  sortBy: 'threshold_gap'
});

// Sample AI Forecast Data
const predictions = ref([
  { 
    name: "Bremžu kluči", vin: "VF312345", sku: "BK-99", warehouse: "Rīga-A", 
    currentStock: 5, aiThreshold: 12, price: 45.50, cv2: 0.15, adi: 1.2, 
    trend: 'Rising', lastOrdered: '2025-4-15', orderQty: 0 
  },
  { 
    name: "Eļļas filtrs", vin: "WBA99887", sku: "EF-002", warehouse: "Ogre-1", 
    currentStock: 45, aiThreshold: 30, price: 8.20, cv2: 0.05, adi: 0.8, 
    trend: 'Stable', lastOrdered: '2025-3-01', orderQty: 0 
  },
  { 
    name: "Zobsiksna", vin: "TMB11223", sku: "ZS-554", warehouse: "Valmiera", 
    currentStock: 2, aiThreshold: 10, price: 120.00, cv2: 0.45, adi: 4.5, 
    trend: 'Falling', lastOrdered: '2026-01-20', orderQty: 0 
  },
  { 
    name: "Eļļas filtrs", vin: "XZC43424", sku: "EF-223", warehouse: "Valmiera", 
    currentStock: 0, aiThreshold: 3, price: 40.00, cv2: 0.34, adi: 1.6, 
    trend: 'Rising', lastOrdered: 'Jauns ieteikums', orderQty: 0 
  }
]);

// --- 2. Configurations ---
const tableCols = [
  { id: 'name', label: 'Nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'warehouse', label: 'Noliktava' },
  { id: 'currentStock', label: 'Pašlaik noliktavā' },
  { id: 'aiThreshold', label: 'MI Slieksnis' },
  { id: 'cv2', label: 'CV^2' },
  { id: 'adi', label: 'ADI' },
  { id: 'trend', label: 'Tendence' },
  { id: 'price', label: 'Cena' },
  { id: 'lastOrdered', label: 'Iepriekš pasūtīts' },
  { id: 'orderQty', label: 'Pasūtīt' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt detaļu' },
  { id: 'serviceLevel', type: 'slider', label: 'Servisa līmenis (%)', min: 90, step: 0.1, max: 99.5 },
  { id: 'thresholdTime', type: 'slider', label: 'Sliekšņa laiks (Dienas)', min: 7, max: 90 },
  // { 
  //   id: 'weighting', type: 'select', label: 'Svērums', 
  //   options: ['Linear', 'Exponential', 'Last 3 Months'] 
  // },
  { id: 'priority', type: 'slider', label: 'Iegādes biežums', min: 90, step: 0.1, max: 99.5 }
];

// --- 3. Actions ---
const handleBulkOrder = () => {
  const itemsToOrder = predictions.value.filter(p => p.orderQty > 0);
  if (itemsToOrder.length === 0) {
    alert("Lūdzu, ievadiet daudzumu vismaz vienai detaļai.");
    return;
  }
  console.log("Processing bulk order for:", itemsToOrder);
  alert(`Pasūtījums veiksmīgi izveidots priekš ${itemsToOrder.length} detaļām!`);
};
</script>

<template>
  <div class="dashboard-layout">
    <NavBar activeTab="AI Predictions" />
    
    <div class="main-container">
      <SideBar v-model="filters" :config="sidebarConfig" />

      <main class="content-area">
        <header class="prediction-header">
          <div>
            <h1 class="text-2xl font-bold">MI Inventāra Prognozes</h1>
            <p class="text-slate-500 text-sm">Automātiski aprēķinātie krājumu sliekšņi optimālai darbībai.</p>
          </div>
        </header>

        <DataTable 
          :columns="tableCols"
          :data="predictions"
          :filters="filters"
          :globalActions="[
            { id: 'order', label: 'Veikt pasūtījumu' },
            { id: 'csv', label: 'Eksportēt datus CSV' }
          ]"
          @globalAction="(id) => id === 'order' ? handleBulkOrder() : null"
        >
          <template #col-currentStock="{ value, item }">
            <span :class="['stock-display', value < item.aiThreshold ? 'critical' : 'stable']">
              {{ value }}
            </span>
          </template>

          <template #col-trend="{ value }">
            <span :class="['trend-icon', value.toLowerCase()]">
              {{ value === 'Rising' ? '↗' : value === 'Falling' ? '↘' : '→' }} {{ value }}
            </span>
          </template>

          <template #col-orderQty="{ item }">
            <input 
              type="number" 
              v-model.number="item.orderQty" 
              class="order-input"
              min="0"
            />
          </template>
        </DataTable>
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex; 
  flex-direction: column; 
  height: 100vh;
}

.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.content-area {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
  background: white;
}

.prediction-header {
  margin-bottom: 30px;
}

.stock-display {
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.stock-display.critical {
  color: #ef4444;
}
.stock-display.stable {
  color: #1e293b;
}

.trend-icon.rising {
  color: #22c55e;
}

.trend-icon.falling {
  color: #ef4444;
}

.trend-icon.stable {
  color: #64748b;
}


.order-input {
  width: 70px;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 600;
  text-align: center;
  outline: none;
}
.order-input:focus {
  border-color: #2563eb;
  background: #eff6ff;
}
</style>