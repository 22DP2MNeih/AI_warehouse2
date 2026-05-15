<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import api from '../services/api';
import { useAuthStore } from '../stores/auth';
const authStore = useAuthStore();

// --- 1. State Management ---
const isCreatingOrder = ref(false);
const orders = ref([]); // Start with empty array
const filters = ref({
  search: '',
  internalOnly: false,
  status: ''
});

// Fetch data on load
const fetchOrders = async () => {
  try {
    const response = await api.getOrders();
    orders.value = response.data;
    console.log(orders);
  } catch (error) {
    console.error("Kļūda ielādējot pasūtījumus:", error);
  }
};

onMounted(() => {
  fetchOrders();
});

// --- 2. Configurations ---
const tableColumns = [
  { id: 'id', label: 'Identifikators' },
  { id: 'part_name', label: 'Detaļas nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'price', label: 'Cena' },
  { id: 'status', label: 'Statuss' },
  { id: 'from_warehouse_name', label: 'No' },
  { id: 'to_warehouse_name', label: 'Uz' },
  { id: 'date', label: 'Datums' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt pasūtījumu', placeholder: 'ID vai VIN...' },
  { id: 'internalOnly', type: 'checkbox', label: 'Iekšējs pasūtījums' },
  { id: 'status', type: 'select', label: 'Filtrēt pēc statusa', options: ['Pending', 'Approved', 'Rejected', 'Completed'] }
];

// --- 3. Logic ---
const handleRowAction = async ({ action, item }) => {
  try {
    if (action === 'approve') {
      await api.approveOrder(item.id);
    } else if (action === 'reject') {
      await api.rejectOrder(item.id);
    } else if (action === 'complete') {
      await api.completeOrder(item.id);
    } else if (action === 'delete') {
      if (confirm('Vai tiešām vēlaties dzēst šo pasūtījumu?')) {
        await api.deleteOrder(item.id);
      }
    }
    // Refresh data after any action
    await fetchOrders();
  } catch (error) {
    console.error(`Darbība ${action} neizdevās:`, error);
  }
};

const handleGlobalAction = (actionId) => {
  if (actionId === 'create') isCreatingOrder.value = true;
  if (actionId === 'import') console.log("Importing CSV...");
};

const handleFormSubmit = async (data) => {
  // Logic for creating order via API would go here
  // For now, keeping your existing logic but wrapping in visibility toggle
  console.log("Form data:", data);
  isCreatingOrder.value = false;
  await fetchOrders();
};

const { user, userRole } = storeToRefs(authStore);
const userMeta = computed(() => {
  return {
    // Access the .value because these are now refs
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});
</script>

<template>
  <div class="dashboard-layout">
    <NavBar :userMeta="userMeta" activeTab="order" />
    
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
              { id: 'approve', label: 'Apstiprināt' },
              { id: 'reject', label: 'Noraidīt' },
              { id: 'complete', label: 'Pabeigt' },
              { id: 'delete', label: 'Dzēst' }
            ]"
            @action="handleRowAction"
            @globalAction="handleGlobalAction"
          >
            <template #col-status="{ value }">
              <span :class="['status-pill', value?.toLowerCase()]">
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
              @cancel="isCreatingOrder = false"
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

.status-pill {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pill.pending { background: #fef3c7; color: #d97706; }
.status-pill.approved { background: #e0f2fe; color: #0369a1; }
.status-pill.rejected { background: #fee2e2; color: #b91c1c; }
.status-pill.completed { background: #dcfce7; color: #16a34a; }
</style>