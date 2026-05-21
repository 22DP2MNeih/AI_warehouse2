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
const { user, userRole } = storeToRefs(authStore);

// --- 1. State Management ---
const isCreatingOrder = ref(false);
const orders = ref([]); 
const warehouses = ref([]);
const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});
const selectedOrder = ref(null);
const actionType = ref(""); // "approve" or "complete"

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
  } catch (error) {
    console.error("Kļūda ielādējot pasūtījumus:", error);
  }
};

const fetchWarehouses = async () => {
  try {
    const response = await api.getWarehouses();
    warehouses.value = response.data;
  } catch (error) {
    console.error("Kļūda ielādējot noliktavas:", error);
  }
};

onMounted(() => {
  fetchOrders();
  fetchWarehouses();
});

// --- 2. Configurations ---
const tableColumns = [
  { id: 'id', label: 'ID' },
  { id: 'part_name', label: 'Detaļa' },
  { id: 'vin', label: 'VIN' },
  { id: 'quantity', label: 'Skaits' },
  { id: 'status', label: 'Statuss' },
  { id: 'from_warehouse_name', label: 'No (Noliktava)' },
  { id: 'to_warehouse_name', label: 'Uz (Noliktava)' },
  { id: 'created_at', label: 'Datums' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt pasūtījumu', placeholder: 'ID vai detaļa...' },
  { id: 'status', type: 'select', label: 'Statuss', placeholder: 'Visi statusi...', options: ['PENDING', 'APPROVED', 'REJECTED', 'COMPLETED'] }
];

// Form fields for picking a warehouse upon approval
const approveFields = computed(() => [
  { id: 'part_name', type: 'text', label: 'Detaļa', disabled: true },
  { id: 'quantity', type: 'number', label: 'Daudzums', disabled: true },
  { 
    id: 'from_warehouse', 
    type: 'select', 
    label: 'Izsniegt no noliktavas', 
    options: warehouses.value.map(w => ({
      label: w.name,      
      key: w.id         
    })),
    required: true 
  }
]);

// Form fields for creating a new order
const orderFormFields = computed(() => [
  { id: 'custom_part_name', type: 'text', label: 'Detaļas nosaukums', required: true },
  { id: 'quantity', type: 'number', label: 'Daudzums', required: true, min: 1 },
  { 
    id: 'to_warehouse', 
    type: 'select', 
    label: 'Mērķa noliktava', 
    options: warehouses.value.map(w => ({
      label: w.name,      
      key: w.id         
    })),
    required: true 
  },
  {
    id: 'order_type',
    type: 'select',
    label: 'Pasūtījuma tips',
    options: [
      { key: 'TRANSFER', label: 'Iekšēja noliktavas kustība' },
      { key: 'CONSUME', label: 'Izlietots remontam' }
    ],
    required: true
  }
]);

// --- 3. Logic ---
const handleRowAction = async ({ action, item }) => {
  try {
    if (action === 'approve') {
      // If order does not specify a warehouse to fulfill from, manager must pick one
      if (!item.from_warehouse) {
        if (warehouses.value.length === 0) {
          alert("Lūdzu, vispirms izveidojiet vismaz vienu noliktavu Noliktavas skatā.");
          return;
        }
        actionType.value = "approve";
        selectedOrder.value = item;
        formTitle.value = "Apstiprināt pasūtījumu (Izvēlēties noliktavu)";
        formFields.value = approveFields.value;
        formData.value = {
          part_name: item.part_name || 'Detaļa',
          quantity: item.quantity || 1,
          from_warehouse: warehouses.value[0]?.id || ''
        };
        formOpen.value = true;
        return;
      }
      
      await api.approveOrder(item.id);
      alert("Pasūtījums veiksmīgi apstiprināts!");
    } else if (action === 'reject') {
      await api.rejectOrder(item.id);
      alert("Pasūtījums noraidīts!");
    } else if (action === 'complete') {
      // If completing a pending order directly without warehouse set
      if (!item.from_warehouse) {
        if (warehouses.value.length === 0) {
          alert("Lūdzu, vispirms izveidojiet vismaz vienu noliktavu Noliktavas skatā.");
          return;
        }
        actionType.value = "complete";
        selectedOrder.value = item;
        formTitle.value = "Pabeigt pasūtījumu (Izvēlēties noliktavu)";
        formFields.value = approveFields.value;
        formData.value = {
          part_name: item.part_name || 'Detaļa',
          quantity: item.quantity || 1,
          from_warehouse: warehouses.value[0]?.id || ''
        };
        formOpen.value = true;
        return;
      }
      await api.completeOrder(item.id);
      alert("Pasūtījums pabeigts un noliktavas krājumi atjaunināti!");
    } else if (action === 'delete') {
      if (confirm('Vai tiešām vēlaties dzēst šo pasūtījumu?')) {
        await api.deleteOrder(item.id);
        alert("Pasūtījums dzēsts.");
      }
    }
    // Refresh data after any action
    await fetchOrders();
  } catch (error) {
    console.error(`Darbība ${action} neizdevās:`, error);
    alert("Darbība neizdevās: " + (error.response?.data?.error || error.message));
  }
};

const handleGlobalAction = (actionId) => {
  if (actionId === 'create') isCreatingOrder.value = true;
  if (actionId === 'import') console.log("Importing CSV...");
};

const handleFormSubmit = async (data) => {
  try {
    await api.createOrder({
      custom_part_name: data.custom_part_name,
      quantity: data.quantity,
      to_warehouse: data.to_warehouse,
      order_type: data.order_type
    });
    alert("Pasūtījums veiksmīgi izveidots!");
    isCreatingOrder.value = false;
    await fetchOrders();
  } catch (error) {
    console.error("Kļūda izveidojot pasūtījumu:", error);
    alert("Kļūda: " + (error.response?.data?.error || error.message));
  }
};

const handleApproveFormSubmit = async (data) => {
  try {
    if (actionType.value === "approve") {
      await api.approveOrder(selectedOrder.value.id, {
        from_warehouse: data.from_warehouse
      });
      alert("Pasūtījums veiksmīgi apstiprināts!");
    } else if (actionType.value === "complete") {
      await api.completeOrder(selectedOrder.value.id, {
        from_warehouse: data.from_warehouse
      });
      alert("Pasūtījums pabeigts un krājumi atjaunināti!");
    }
    formOpen.value = false;
    await fetchOrders();
  } catch (error) {
    console.error("Kļūda apstiprinot pasūtījumu:", error);
    alert("Darbība neizdevās: " + (error.response?.data?.error || error.message));
  }
};

const userMeta = computed(() => {
  return {
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="order" />
    
    <div class="content-body">
      <SideBar 
        v-model="filters" 
        :config="sidebarConfig" 
        title="Filtri"
      />

      <main class="main-content">
        <template v-if="!isCreatingOrder && !formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">Pasūtījumu saraksts</h1>
              <p class="view-subtitle">Skatiet veiktos pasūtījumus</p>
            </div>
          </div>

          <DataTable 
            :columns="tableColumns"
            :data="orders"
            :filters="filters"
            :globalActions="[
              { id: 'create', label: 'Veikt pasūtījumu' }
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

        <template v-else-if="formOpen">
          <div class="form-wrapper">
            <DynamicForm 
              :title="formTitle"
              :fields="formFields"
              :initialData="formData"
              submitLabel="Apstiprināt pasūtījumu"
              @submit="handleApproveFormSubmit"
              @cancel="formOpen = false"
            />
          </div>
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
.dashboard-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
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

.main-content {
  flex: 1;
  padding: 2rem 0rem 0rem 3rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

:deep(.sidebar-container) {
  width: 320px;
  border-right: 1px solid #e2e8f0;
  background: white;
}

.content-area {
  flex: 1;
  padding: 40px;
  /* overflow-y: hidden; */
  background-color: #f8fafc;
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