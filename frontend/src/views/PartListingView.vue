<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import api from '../services/api';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue'; // 1. Import DynamicForm
import { useAuthStore } from '../stores/auth';


// --- State Management ---
const authStore = useAuthStore();
const inventory = ref([]);
const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});
const actionType = ref("");
const selectedItem = ref(null);
const { user, userRole } = storeToRefs(authStore);
const userMeta = computed(() => {
  return {
    // Access the .value because these are now refs
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});

// --- Form Blueprints ---
const orderFields = [
  { id: 'product_name', type: 'text', label: 'Detaļa', disabled: true },
  { id: 'sku', type: 'text', label: 'SKU', disabled: true },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 1, required: true },
  { id: 'notes', type: 'textarea', label: 'Piezīmes', fullWidth: true },
];

const addPartFields = [
  { id: 'product_name', type: 'text', label: 'Nosaukums', required: true },
  { id: 'product_vin', type: 'text', label: 'VIN', required: true },
  { id: 'sku', type: 'text', label: 'SKU', required: true },
  { id: 'price', type: 'float', label: 'Cena', required: true },
  { id: 'description', type: 'textarea', label: 'Apraksts', fullWidth: true },
];

// --- Existing Configurations ---
const sidebarConfig = ref([
  { id: 'name', type: 'text', label: 'Nosaukums' },
  { id: 'vin', type: 'text', label: 'VIN' },
  { id: 'sku', type: 'text', label: 'SKU' },
  { id: 'company', type: 'text', label: 'Uzņēmums' },
]);

const tableColumns = ref([
  { id: 'product_name', label: 'Nosaukums', sortable: true },
  { id: 'product_vin', label: 'VIN', sortable: true },
  { id: 'sku', label: 'SKU', sortable: true },
  { id: 'company_name', label: 'Uzņēmums', sortable: true },
  { id: 'price', label: 'Cena', sortable: true }
]);

const rowActions = ref([{ id: 'order', label: 'Pasūtīt' }]);
const filters = ref({ name: '', vin: '', sku: '', company: '' });

// --- Logic ---
const fetchMarketData = async () => {
  try {
    const res = await api.getMarket();
    inventory.value = res.data.map(part => ({ ...part, price: Number(part.price) }));
  } catch (err) {
    console.error("Failed to load market data:", err);
  }
};

onMounted(fetchMarketData);

const processedData = computed(() => {
  return inventory.value.filter(item => {
    const f = filters.value;
    return item.product_name?.toLowerCase().includes(f.name.toLowerCase()) &&
           item.product_vin?.toLowerCase().includes(f.vin.toLowerCase()) &&
           item.sku?.toLowerCase().includes(f.sku.toLowerCase()) &&
           item.company_name?.toLowerCase().includes(f.company.toLowerCase());
  });
});

// --- Event Handlers ---
const openAddPartForm = () => {
  actionType.value = "add_part";
  formTitle.value = "Pievienot jaunu detaļu tirgum";
  formFields.value = addPartFields;
  formData.value = {};
  formOpen.value = true;
};

const handleAction = ({ action, item }) => {
  console.log("action called:", action, item); // console says "action called: undefined undefined"
      
  if (action === 'order') {
    console.log(item);
    selectedItem.value = item;
    actionType.value = "order_part";
    formTitle.value = `Pasūtīt detaļu: ${item.product_name}`;
    formFields.value = orderFields;
    formData.value = {
      product_name: item.product_name,
      sku: item.sku,
      quantity: 1
    };
    formOpen.value = true;
  }
};

const handleSave = async (newData) => {
  try {
    if (actionType.value === "order_part") {
      // Logic for creating an order from the market
      await api.createOrder({
        product_listing: selectedItem.value.id,
        quantity: newData.quantity,
        order_type: "PURCHASE",
        notes: newData.notes,
        // from_warehouse: selectedItem.value.,
      });
    } // else if (actionType.value === "add_part") {
    //   await api.createMarketListing(newData);
    // }
    
    formOpen.value = false;
    await fetchMarketData(); // Refresh list
  } catch (err) {
    console.error("Form submission error:", err);
  }
};

const closeForm = () => {
  formOpen.value = false;
};
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="Inventory" />

    <div class="content-body">
      <SideBar v-model="filters" :config="sidebarConfig" />

      <!-- Toggle between Table and Form -->
      <main class="main-content">
        <template v-if="!formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">Detaļu Noliktava</h1>
              <p class="view-subtitle">Pārvaldiet krājumus un pasūtījumus</p>
            </div>
            <div class="view-actions">
              <!-- Connect the Add Button -->
              <button class="btn-add" @click="openAddPartForm">+ Pievienot jaunu detaļu</button>
            </div>
          </div>

          <DataTable 
            :columns="tableColumns" 
            :data="processedData" 
            :rowActions="rowActions"
            @action="handleAction"
          />
        </template>

        <!-- Dynamic Form Rendering -->
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
