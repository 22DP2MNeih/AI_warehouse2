<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import api from '../services/api';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';


const authStore = useAuthStore();
console.log(authStore);

const canAddPart = computed(() => {
    return ['ADMIN', 'CEO', 'WAREHOUSE_MANAGER'].includes(authStore.userRole);
});

const canRequestPart = computed(() => {
    return authStore.userRole === 'MECHANIC';
});
// const response = await api.getInventory();
// console.log(response.data);
const inventory = ref([]);
const warehouses = ref([]);

onMounted(async () => {
    try {
        const [inventoryRes, warehouseRes] = await Promise.all([
            api.getInventory(),
            api.getWarehouses()
        ]);
        
        inventory.value = inventoryRes.data;
        warehouses.value = warehouseRes.data; // Fill the ref
    } catch (err) {
        // 4. Use translation in JS logic
        // error.value = t.value('inventory.errorLoad'); 
        console.error(err);
    } finally {
        // loading.value = false;
    }
});

const handleDeleted = (id) => {
    parts.value = parts.value.filter(p => p.id !== id);
};

const handleUpdate = async () => {
    try {
        const response = await api.getInventory();
        parts.value = response.data;
    } catch (err) {
        console.error(err);
    }
};

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
  { id: 'transfer_part', label: 'Parvietot' },
];
const rowActionsMech = [
  { id: 'transfer_part', label: 'Izveidot pasūtījumu' },
  { id: 'use_part', label: 'Izmantot detaļu' },
];

const rowActions = computed( () => {
  console.log(authStore.userRole);
  return canAddPart.value? rowActionsWHMngr : rowActionsMech;
})

const myGlobalActions = [
  { id: 'add-part', label: 'Pievienot detaļu' },
  { id: 'export', label: 'Eksportēt CSV' },
  { id: 'import', label: 'Importēt CSV' }
];

const action_type = ref("");
const last_part = ref({});

const handleGlobalAction = (id) => {
  if (id === 'add-part') {
    formTitle.value = "Pievienot Detaļu";
    action_type.value = id;
    formFields.value = inventoryFields.value;
    formOpen.value = true; 
  }
};

const formOpen = ref(false);
const formData = ref({});
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
    id: 'warehouse_id', // Pro-tip: Changed to _id since you'll likely save the ID, not the name
    type: 'select', 
    label: 'Noliktava', 
    // Map the raw data to Label/Value pairs
    options: warehouses.value.map(w => ({
      label: w.name,      // What the user sees in the dropdown
      key: w.id         // What gets sent to the database
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
    required: false // Optional: Django will auto-assign if left blank
  },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 0, step: 0.001, required: true },
]);

const formFields = ref([]);

const formTitle = ref("");
const handleAction = ({ action, item }) => {
  if (!item) return;
  
  last_part.value = item;
  action_type.value = action;
  
  if (action === 'use_part') {
    formTitle.value = "Izmantot Detaļu"
    formFields.value = consumeFields;
    formData.value = {
      part_name: item.product_name,
      vin_input: item.vin,
      quantity: 1
    };
    formOpen.value = true;
  } else if (action === 'transfer_part') {
    formTitle.value = "Pārvietot Detaļu"
    formFields.value = transferFields.value; // Use the computed value
    formData.value = {
      part_name: item.product_name,
      vin_input: item.vin,
      from_warehouse: item.warehouse_name, // Displayed in disabled text field
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
        // If to_warehouse is null, Django perform_create sets it to user.warehouse
        to_warehouse: newData.to_warehouse || null 
      };
      
      await api.createOrder(apiData);
    }

    // Common cleanup after any successful action
    formOpen.value = false;
    const inventoryRes = await api.getInventory();
    inventory.value = inventoryRes.data;

  } catch (err) {
    console.error(`Error executing ${action_type.value}:`, err);
    // You could add a toast notification here
  }
};

const createAndCompleteOrder = async (apiData) => {
  const response = await api.createOrder(apiData);
  api.completeOrder(response.data.id);
};

const closeForm = () => {
  formOpen.value = false;
};
const { user, userRole } = storeToRefs(authStore);
const userMeta = computed(() => {
  return {
    // Access the .value because these are now refs
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});
console.log(rowActions);
</script>

<template>
  <div class="app-wrapper">
     <SideBar 
      v-model="activeFilters" 
      :config="sidebarConfig" 
    />
    <main v-if="!formOpen">
      <NavBar :userMeta="userMeta" activeTab="warehouse"/>
      <div class="page-content">
        <DataTable 
          :columns="tableCols" 
          :data="inventory"
          :rowActions="rowActions"
          :globalActions="myGlobalActions"
          @action="handleAction"
          @globalAction="handleGlobalAction"
        />
      </div>
    </main>
    <main v-else class="flex justify-center pt-10">
      <DynamicForm 
        :title="formTitle"
        :fields="formFields"
        :initialData="formData"
        @submit="handleSave"
        @cancel="closeForm"
      />
    </main>
  </div>
</template>

<style>
:root {
  --bg-color: #f8fafc;
  --primary-blue: #2563eb;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
}

.app-wrapper {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
}

main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.page-content {
  padding: 40px;
}
</style>