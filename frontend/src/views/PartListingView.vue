<script setup>
import { ref, computed } from 'vue';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';

// 1. Meta Data & Auth State
const userMeta = ref({
  name: 'Jānis Bērziņš',
  role: 'Noliktavas Vadītājs'
});

// 2. Sidebar Configuration (Contextual Controller)
const sidebarConfig = ref([
  { id: 'name', type: 'text', label: 'Nosaukums' },
  { id: 'vin', type: 'text', label: 'VIN' },
  { id: 'sku', type: 'text', label: 'SKU' },
  { id: 'warehouse', type: 'text', label: 'Noliktava' },
  { id: 'company', type: 'text', label: 'Uzņēmums' },
  { id: 'onlyCurrentCompany', type: 'checkbox', label: 'Tikai šis uzņēmums' }
]);

// 3. DataTable Configuration
const tableColumns = ref([
  { id: 'name', label: 'Nosaukums', sortable: true },
  { id: 'vin', label: 'VIN', sortable: true },
  { id: 'sku', label: 'SKU', sortable: true },
  { id: 'stockStatus', label: 'Noliktavā / AI Floor', sortable: false },
  { id: 'location', label: 'Atrašanās vieta', sortable: true },
  { id: 'price', label: 'Cena', sortable: true }
]);

// Row Actions (Excluding "Izmantot" as per request)
const rowActions = ref([
  { id: 'order', label: 'Pasūtīt', class: 'btn-primary' },
  { id: 'move', label: 'Pārvietot', class: 'btn-secondary' }
]);

// 4. Reactive State & Data
const filters = ref({
  name: '',
  vin: '',
  sku: '',
  warehouse: '',
  company: '',
  onlyCurrentCompany: false
});

const inventory = ref([
  {
    id: 1,
    name: 'Bremžu diski (Priekšējie)',
    vin: 'WBA312000L123456',
    sku: 'BD-2210-XL',
    currentStock: 2,
    recommendedStock: 5,
    company: 'Auto Stars SIA',
    warehouse: 'A-Sekcija',
    price: 120.50,
    location: 'A-Sekcija / Auto Stars SIA'
  },
  {
    id: 2,
    name: 'Eļļas filtrs',
    vin: 'ANY-VIN-7788',
    sku: 'EF-551',
    currentStock: 12,
    recommendedStock: 10,
    company: 'Auto Stars SIA',
    warehouse: 'B-Sekcija',
    price: 12.00,
    location: 'B-Sekcija / Auto Stars SIA'
  },
  {
    id: 3,
    name: 'Amortizators (Aizmugurējais)',
    vin: 'VAG9900112233',
    sku: 'AM-99-R',
    currentStock: 0,
    recommendedStock: 4,
    company: 'Auto Stars SIA',
    warehouse: 'A-Sekcija',
    price: 89.99,
    location: 'A-Sekcija / Auto Stars SIA'
  }
]);

// 5. Logic: Process Data (Filtering)
const processedData = computed(() => {
  return inventory.value.map(item => {
    // Dynamically calculate status for display
    return {
      ...item,
      stockStatus: `${item.currentStock} / ${item.recommendedStock}`,
      isLowStock: item.currentStock < item.recommendedStock
    };
  }).filter(item => {
    const f = filters.value;
    const matchName = item.name.toLowerCase().includes(f.name.toLowerCase());
    const matchVin = item.vin.toLowerCase().includes(f.vin.toLowerCase());
    const matchSku = item.sku.toLowerCase().includes(f.sku.toLowerCase());
    const matchWarehouse = item.warehouse.toLowerCase().includes(f.warehouse.toLowerCase());
    const matchCompany = item.company.toLowerCase().includes(f.company.toLowerCase());
    
    return matchName && matchVin && matchSku && matchWarehouse && matchCompany;
  });
});

// Event Handlers
const handleAction = ({ actionId, row }) => {
  console.log(`Action ${actionId} triggered for part: ${row.sku}`);
};
</script>

<template>
  <div class="app-layout">
    <!-- Fixed Navigation -->
    <NavBar :userMeta="userMeta" activeTab="Inventory" />

    <div class="content-body">
      <!-- Contextual Controller -->
      <SideBar 
        v-model="filters" 
        :config="sidebarConfig" 
      />

      <!-- Polymorphic Main Area -->
      <main class="main-content">
        <div class="view-header">
          <div class="header-titles">
            <h1 class="view-title">Detaļu Noliktava</h1>
            <p class="view-subtitle">Pārvaldiet krājumus un pasūtījumus</p>
          </div>
          <div class="view-actions">
            <button class="btn-add">+ Pievienot jaunu detaļu</button>
          </div>
        </div>

        <DataTable 
          :columns="tableColumns" 
          :data="processedData" 
          :rowActions="rowActions"
          @action="handleAction"
        >
          <!-- Custom Slot for the 0/0 Stock display -->
          <template #cell-stockStatus="{ row }">
            <div class="stock-container">
              <span :class="['stock-badge', row.isLowStock ? 'critical' : 'optimal']">
                {{ row.stockStatus }}
              </span>
              <div v-if="row.isLowStock" class="ai-warning">
                Zems krājums
              </div>
            </div>
          </template>
        </DataTable>
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

.content-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

:deep(.sidebar-container) {
  width: 320px;
  border-right: 1px solid #e2e8f0;
  background: white;
}

.main-content {
  flex: 1;
  padding: 2rem 3rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.view-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.view-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
}

.btn-add {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1), 0 2px 4px -1px rgba(37, 99, 235, 0.06);
}

.btn-add:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

.stock-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-badge {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-weight: 700;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  display: inline-block;
  text-align: center;
  font-size: 0.9rem;
}

.stock-badge.critical {
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fee2e2;
}

.stock-badge.optimal {
  color: #059669;
  background: #ecfdf5;
  border: 1px solid #d1fae5;
}

.ai-warning {
  font-size: 0.7rem;
  color: #dc2626;
  font-weight: 600;
  text-transform: uppercase;
}

:root {
  --accent-blue: #2563eb;
}
</style>