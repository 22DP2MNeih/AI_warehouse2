<script setup>
import { ref, computed } from 'vue';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';

// --- 1. State Management ---
const isCreatingOrder = ref(false);
const filters = ref({
  search: '',
  internalOnly: false,
  status: ''
});

// Sample Data
const orders = ref([
  { id: 'ORD-7721', part: 'Eļļas filtrs', vin: 'WBA12345678', sku: 'EF-99', price: 12.40, status: 'Pending', from: 'Noliktava A', to: 'Serviss Centrs', date: '2025-11-28' },
  { id: 'ORD-8802', part: 'Zobsiksna', vin: 'VF388221100', sku: 'ZS-01', price: 89.99, status: 'Completed', from: 'Galvenā Noliktava', to: 'Noliktava B', date: '2025-11-25' },
]);

// --- 2. Configurations ---
const tableColumns = [
  { id: 'id', label: 'Identifikators' },
  { id: 'part', label: 'Detaļas nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'price', label: 'Cena' },
  { id: 'status', label: 'Statuss' },
  { id: 'from', label: 'No' },
  { id: 'to', label: 'Uz' },
  { id: 'date', label: 'Datums' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt pasūtījumu', placeholder: 'ID vai VIN...' },
  { id: 'internalOnly', type: 'checkbox', label: 'Iekšējs pasūtījums' },
  { id: 'status', type: 'select', label: 'Filtrēt pēc statusa', options: ['Pending', 'Completed'] }
];

const orderFormFields = [
  { id: 'part', type: 'text', label: 'Detaļas nosaukums', required: true },
  { id: 'vin', type: 'text', label: 'Automašīnas VIN', required: true },
  { id: 'from', type: 'select', label: 'Izsūtītāja Noliktava', options: ['Noliktava A', 'Galvenā Noliktava'], required: true },
  { id: 'to', type: 'select', label: 'Saņēmēja Noliktava', options: ['Serviss Centrs', 'Noliktava B'], required: true },
  { id: 'price', type: 'number', label: 'Vērtība (€)', required: true },
  { id: 'notes', type: 'textarea', label: 'Piezīmes', fullWidth: true }
];

// --- 3. Logic ---
const handleRowAction = ({ action, item }) => {
  if (action === 'complete') {
    const target = orders.value.find(o => o.id === item.id);
    if (target) target.status = 'Completed';
  }
};

const handleGlobalAction = (actionId) => {
  if (actionId === 'create') isCreatingOrder.value = true;
  if (actionId === 'import') console.log("Importing CSV...");
};

const handleFormSubmit = (data) => {
  const newOrder = {
    id: `ORD-${Math.floor(Math.random() * 9000) + 1000}`,
    status: 'Pending',
    date: new Date().toISOString().split('T')[0],
    ...data
  };
  orders.value.unshift(newOrder);
  isCreatingOrder.value = false;
};
</script>

<template>
  <div class="dashboard-layout">
    <NavBar activeTab="Orders" />
    
    <div class="main-container">
      <SideBar 
        v-model="filters" 
        :config="sidebarConfig" 
      />

      <main class="content-area">
        <template v-if="!isCreatingOrder">
          <DataTable 
            :columns="tableColumns"
            :data="orders"
            :filters="filters"
            :globalActions="[
              { id: 'create', label: 'Veikt pasūtījumu' },
              { id: 'import', label: 'Importēt CSV' },
              { id: 'export', label: 'Eksportēt CSV' }
            ]"
            :rowActions="[
              { id: 'complete', label: 'Pabeigt pasūtījumu' }
            ]"
            @action="handleRowAction"
            @globalAction="handleGlobalAction"
          >
            <template #col-status="{ value }">
              <span :class="['status-pill', value.toLowerCase()]">
                {{ value }}
              </span>
            </template>
          </DataTable>
        </template>

        <template v-else>
          <div class="form-wrapper">
            <DynamicForm 
              title="Jauna pasūtījuma izveide"
              :fields="orderFormFields"
              submitLabel="Apstiprināt pasūtījumu"
              @submit="handleFormSubmit"
              @cancel="isCreatingOrder.value = false"
            />
          </div>
        </template>
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
  background-color: #ffffff;
}

.form-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}

/* Status Specific Styling */
.status-pill {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pill.pending {
  background: #fef3c7;
  color: #d97706;
}

.status-pill.completed {
  background: #dcfce7;
  color: #16a34a;
}
</style>