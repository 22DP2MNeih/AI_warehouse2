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

// --- Reactive State for Filters ---
const activeFilters = ref({
  product_name: '',
  vin: '',
  sku: '',
  warehouse_id: '',
  company_name: '',
  location: ''
});

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

// --- Dynamic Sidebar Configuration ---
const sidebarConfig = computed(() => [
  { id: 'product_name', type: 'text', label: 'Detaļas nosaukums' },
  { id: 'vin', type: 'text', label: 'VIN kods' },
  { id: 'sku', type: 'text', label: 'SKU kods' },
  { 
    id: 'warehouse_id', 
    type: 'select', 
    label: 'Noliktava', 
    options: warehouses.value.map(w => ({
      key: w.id,
      label: w.name
    }))
  },
  { id: 'company_name', type: 'text', label: 'Kompānijas Nosaukums' },
  { id: 'location', type: 'text', label: 'Novietojuma kods' },
]);

// --- Table Configuration ---
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

const myGlobalActions = computed(() => {
  const actions = [
    { id: 'export', label: 'Eksportēt CSV' }
  ];
  if (canAddPart.value) {
    actions.unshift({ id: 'add-part', label: 'Pievienot detaļu' });
    actions.push({ id: 'import', label: 'Importēt CSV' });
  }
  return actions;
});

// --- Client-Side Filtering Engine ---
const filteredInventory = computed(() => {
  return inventory.value.filter(item => {
    // 1. Filter by Product Name
    if (activeFilters.value.product_name && 
        !item.product_name?.toLowerCase().includes(activeFilters.value.product_name.toLowerCase())) {
      return false;
    }
    // 2. Filter by VIN
    if (activeFilters.value.vin && 
        !item.vin?.toLowerCase().includes(activeFilters.value.vin.toLowerCase())) {
      return false;
    }
    // 3. Filter by SKU
    if (activeFilters.value.sku && 
        !item.sku?.toLowerCase().includes(activeFilters.value.sku.toLowerCase())) {
      return false;
    }
    // 4. Filter by Warehouse ID
    if (activeFilters.value.warehouse_id) {
      // Find matching warehouse object from the warehouses pool to compare against row data strings
      const targetWarehouse = warehouses.value.find(w => w.id === activeFilters.value.warehouse_id);
      if (targetWarehouse && item.warehouse_name !== targetWarehouse.name) {
        return false;
      }
    }
    // 5. Filter by Company Name (If provided in item fields)
    if (activeFilters.value.company_name && 
        !item.company_name?.toLowerCase().includes(activeFilters.value.company_name.toLowerCase())) {
      return false;
    }
    // 6. Filter by Location
    if (activeFilters.value.location && 
        !item.location?.toLowerCase().includes(activeFilters.value.location.toLowerCase())) {
      return false;
    }
    return true;
  });
});

// --- Form Blueprints ---
const consumeFields = [
  { id: 'part_name', type: 'text', label: 'Detaļas Nosaukums', disabled: true },
  { id: 'vin_input', type: 'text', label: 'VIN Kods', disabled: true },
  { id: 'used_on', type: 'textarea', label: 'Detaļa izmantota auto', required: true, maxCharacters: 255 },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 0, max: 1, step: 0.001, required: true },
];

const inventoryFields = computed(() => [
  { id: 'name', type: 'text', label: 'Detaļas Nosaukums', required: true, maxCharacters: 255 },
  { id: 'sku_input', type: 'text', label: 'SKU Kods', required: true, maxCharacters: 255 },
  { id: 'location', type: 'text', label: 'Novietojums', required: true, maxCharacters: 100 },
  { id: 'vin_input', type: 'text', label: 'VIN Kods', required: true, maxCharacters: 17 },
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
  { id: 'description_input', type: 'textarea', label: 'Papildus Apraksts', fullWidth: true, maxCharacters: 255 },
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
const handleGlobalAction = async (id) => {
  if (id === 'add-part') {
    formTitle.value = "Pievienot Detaļu";
    action_type.value = id;
    formFields.value = inventoryFields.value;
    formOpen.value = true; 
  } else if (id === 'export') {
    try {
      const response = await api.exportPartsCsv();
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'warehouse_inventory.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("CSV Export failed:", err);
      alert("Kļūda eksportējot datus: " + (err.response?.data?.error || "Mēģiniet vēlreiz."));
    }
  } else if (id === 'import') {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.csv';
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      try {
        const response = await api.importPartsCsv(file);
        const inventoryRes = await api.getInventory();
        inventory.value = inventoryRes.data;
        
        const createdCount = response.data.created || 0;
        const updatedCount = response.data.updated || 0;
        const errors = response.data.errors || [];
        
        let message = `Imports pabeigts!\nIzveidoti: ${createdCount} jauni ieraksti\nAtjaunināti: ${updatedCount} ieraksti`;
        if (errors.length > 0) {
          message += `\n\nKļūdas (${errors.length}):\n` + errors.slice(0, 5).join('\n');
          if (errors.length > 5) {
            message += `\n... un vēl ${errors.length - 5} kļūdas`;
          }
        }
        alert(message);
      } catch (err) {
        console.error("CSV Import failed:", err);
        alert("Kļūda importējot datus: " + (err.response?.data?.error || "Pārbaudiet faila struktūru."));
      }
    };
    fileInput.click();
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
    formFields.value = formFields.value.map(field => 
        field.id === 'quantity' ? { ...field, max: item.quantity } : field
    );
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
          </div>

          <DataTable 
            :columns="tableCols" 
            :data="filteredInventory"
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