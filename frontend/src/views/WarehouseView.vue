<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import api from '../services/api';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';

// --- State Management ---
const authStore = useAuthStore();
const { user, userRole } = storeToRefs(authStore);

const inventory = ref([]);
const warehouses = ref([]);
const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});
const action_type = ref("");
const last_part = ref({});

// --- Authorization Computed Properties ---
const canAddPart = computed(() => {
  return ['ADMIN', 'CEO', 'WAREHOUSE_MANAGER'].includes(authStore.userRole);
});

const canRequestPart = computed(() => {
  return authStore.userRole === 'MECHANIC';
});

const userMeta = computed(() => {
  return {
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});

// --- Existing Configurations ---
const sidebarConfig = [
  { id: 'company_name', type: 'text', label: 'Kompānijas Nosaukums' },
  { id: 'location', type: 'text', label: 'Atrašanās vieta' },
];

const tableCols = [
  { id: 'product_name', label: 'Nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'warehouse_name', label: 'Noliktava'},
  { id: 'quantity', label: 'Pieejams'},
  { id: 'location', label: 'Novietojuma kods' },
  { id: 'description', label: 'Apraksts' },
  { id: 'price', label: 'Cena'}
];

const rowActionsWHMngr = [
  { id: 'transfer_part', label: 'Pārvietot' },
];
const rowActionsMech = [
  { id: 'transfer_part', label: 'Izveidot pasūtījumu' },
  { id: 'use_part', label: 'Izmantot detaļu' },
];

const rowActions = computed(() => {
  return canAddPart.value ? rowActionsWHMngr : rowActionsMech;
});

const myGlobalActions = [
  { id: 'add-part', label: 'Pievienot detaļu' },
  { id: 'export', label: 'Eksportēt CSV' },
  { id: 'import', label: 'Importēt CSV' }
];

// --- Form Blueprints ---
const consumeFields = [
  { id: 'part_name', type: 'text', label: 'Detaļas Nosaukums', disabled: true },
  { id: 'vin_input', type: 'text', label: 'VIN Kods', disabled: true },
  { id: 'used_on', type: 'text', label: 'Detaļa izmantota auto', required: true },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 0, step: 0.001, required: true },
];

const inventoryFields = computed(() => [
  { id: 'name', type: 'text', label: 'Detaļas Nosaukums', required: true },
  { id: 'sku_input', type: 'text', label: 'SKU Kods', required: true },
  { id: 'location', type: 'text', label: 'Novietojums', required: true },
  { id: 'vin_input', type: 'text', label: 'VIN Kods', required: true },
  { 
    id: 'warehouse_id', 
    type: 'select', 
    label: 'Noliktava', 
    options: warehouses.value.map(w => ({
      label: w.name,      
      key: w.id         
    })),
    required: true 
  },
  { id: 'price_input', type: 'float', label: 'Cena (€)', min: 0, step: 0.01, required: true },
  { id: 'sharing_mode_input', type: 'select', label: 'Dalšanās veids', options: [
    {key: 'INTERNAL', label: 'Tikai iekšējs'},
    {key: 'WAREHOUSE_LIMIT', label: 'MI sliekšņa pārpalikums'}, 
    {key: 'MARKET_FIXED', label: 'Fiksēts skaitlis'}, 
    {key: 'GLOBAL', label: 'Visas detaļas ārējas'}
  ], required: true },
  { id: 'sharing_value_input', type: 'float', label: 'Dalšanās skaits', min: 0, step: 0.00001 },
  { id: 'description_input', type: 'textarea', label: 'Papildus Apraksts', fullWidth: true },
]);

const transferFields = computed(() => [
  { id: 'part_name', type: 'text', label: 'Detaļas Nosaukums', disabled: true },
  { id: 'vin_input', type: 'text', label: 'VIN Kods', disabled: true },
  { id: 'from_warehouse', type: 'text', label: 'Noliktava no', disabled: true },
  { 
    id: 'to_warehouse', 
    type: 'select', 
    label: 'Noliktava uz (Pēc noklusējuma: Mana noliktava)', 
    options: warehouses.value.map(w => ({
      label: w.name,
      key: w.id
    })),
    required: false 
  },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 0, step: 0.001, required: true },
]);

// --- Logic ---
onMounted(async () => {
  try {
    const [inventoryRes, warehouseRes] = await Promise.all([
      api.getInventory(),
      api.getWarehouses()
    ]);
    
    inventory.value = inventoryRes.data;
    warehouses.value = warehouseRes.data;
  } catch (err) {
    console.error(err);
  }
});

// --- Event Handlers ---
const handleGlobalAction = (id) => {
  if (id === 'add-part') {
    formTitle.value = "Pievienot Detaļu";
    action_type.value = id;
    formFields.value = inventoryFields.value;
    formOpen.value = true; 
  }
};

const handleAction = ({ action, item }) => {
  if (!item) return;
  
  last_part.value = item;
  action_type.value = action;
  
  if (action === 'use_part') {
    formTitle.value = "Izmantot Detaļu";
    formFields.value = consumeFields;
    formData.value = {
      part_name: item.product_name,
      vin_input: item.vin,
      quantity: 1
    };
    formOpen.value = true;
  } else if (action === 'transfer_part') {
    formTitle.value = "Pārvietot Detaļu";
    formFields.value = transferFields.value;
    formData.value = {
      part_name: item.product_name,
      vin_input: item.vin,
      from_warehouse: item.warehouse_name,
      quantity: 1
    };
    formOpen.value = true;
  }
};

const handleSave = async (newData) => {
  try {
    if (action_type.value === "add-part") {
      await api.createPart(newData);
    } 
    else if (action_type.value === "use_part") {
      const warehouse = warehouses.value.find(w => w.name === last_part.value.warehouse_name);
      const apiData = {
        order_type: "CONSUME",
        product_listing: last_part.value.company_product,
        quantity: newData.quantity,
        destination_external: newData.used_on,
        from_warehouse: warehouse?.id
      };
      await createAndCompleteOrder(apiData);
    } 
    else if (action_type.value === "transfer_part") {
      const sourceWarehouse = warehouses.value.find(w => w.name === last_part.value.warehouse_name);
      const apiData = {
        order_type: "TRANSFER",
        product_listing: last_part.value.company_product,
        quantity: newData.quantity,
        from_warehouse: sourceWarehouse?.id,
        to_warehouse: newData.to_warehouse || null 
      };
      
      await api.createOrder(apiData);
    }

    formOpen.value = false;
    const inventoryRes = await api.getInventory();
    inventory.value = inventoryRes.data;

  } catch (err) {
    console.error(`Error executing ${action_type.value}:`, err);
  }
};

const createAndCompleteOrder = async (apiData) => {
  const response = await api.createOrder(apiData);
  await api.completeOrder(response.data.id);
};

const closeForm = () => {
  formOpen.value = false;
};

// Placeholder filters to avoid template issues if SideBar expects v-model
const activeFilters = ref({});
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="warehouse" />

    <div class="content-body">
      <SideBar v-model="activeFilters" :config="sidebarConfig" />

      <main class="main-content">
        <template v-if="!formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">Noliktavas Inventārs</h1>
              <p class="view-subtitle">Pārvaldiet uzņēmuma detaļas un pārvietojumus</p>
            </div>
            <div class="view-actions" v-if="canAddPart">
              <button class="btn-add" @click="handleGlobalAction('add-part')">
                + Pievienot detaļu
              </button>
            </div>
          </div>

          <DataTable 
            :columns="tableCols" 
            :data="inventory"
            :rowActions="rowActions"
            :globalActions="myGlobalActions"
            @action="handleAction"
            @globalAction="handleGlobalAction"
          />
        </template>

        <div v-else class="form-container">
          <DynamicForm 
            :title="formTitle"
            :fields="formFields"
            :initialData="formData"
            @submit="handleSave"
            @cancel="closeForm"
          />
        </div>
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

.form-container {
  display: flex;
  justify-content: center;
  padding-top: 2.5rem;
}
</style>