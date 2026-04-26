<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../services/api';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';


const authStore = useAuthStore();

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
  // { id: 'postal_code', type: 'text', label: 'Pasta indekss' },
  // { id: 'service_level', type: 'slider', label: 'Servisa Līmenis', modelValue: 97.8, min: 90, max: 99.5, step: 0.1, unit: '%' },
  // { id: 'weight', type: 'slider', label: 'Svērums', modelValue: 93.6, min: 90, max: 99.5, step: 0.1, unit: '%' },
  // { id: 'procurement_priorities', type: 'slider', label: 'Iegādes prioritātes', modelValue: 95.9, min: 90, max: 99.5, step: 0.1, unit: '%' },
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

// let inventory = [
//   { name: "Bremžu kluči", vin: "VF312345678", sku: "BK-9901", warehouse: "Rīga-A", available: 12, locCode: "A-12-3", desc: "Priekšējie keramiskie", price: 45.50 },
//   { name: "Eļļas filtrs", vin: "WBA998877", sku: "EF-002", warehouse: "Rīga-A", available: 45, locCode: "B-01-1", desc: "Sintētiskajai eļļai", price: 8.20 },
//   { name: "Zobsiksna", vin: "TMB112233", sku: "ZS-554", warehouse: "Ogre-1", available: 3, locCode: "C-05-9", desc: "Pastiprinātā", price: 120.00 },
//   { name: "Aizdedzes svece", vin: "UU1223344", sku: "AS-12", warehouse: "Rīga-A", available: 24, locCode: "A-02-1", desc: "Iridija", price: 15.00 },
//   { name: "Gaisa filtrs", vin: "VF312345678", sku: "GF-77", warehouse: "Valmiera", available: 8, locCode: "V-09-2", desc: "Standarta", price: 12.50 },
//   { name: "Amortizators", vin: "WBA998877", sku: "AM-100", warehouse: "Rīga-B", available: 4, locCode: "X-01-4", desc: "Gāzes, aizmugurējais", price: 85.00 }
// ];

// const myRowActions = [
//   { id: 'use_part', label: 'Izmantot detaļu' },
//   { id: 'delete', label: 'Dzēst', class: 'btn-danger' }
// ];
const rowActionsWHMngr = [
  { id: 'order', label: 'Izveidot pasūtījumu' },
];
const rowActionsMech = [
  { id: 'order', label: 'Izveidot pasūtījumu' },
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

const handleAction = ({ action, item }) => {
  if (!item) {
    console.log(`No item`);
    return;
  }
  console.log(`Executing ${action} for`, item.product_name);
  if (action === 'use_part') {
    // Logic for deleting
  }
};

const handleGlobalAction = (id) => { // Usually passed as a single ID/string from the component
  console.log(`Executing global ${id}`);
  
  if (id === 'add-part') {
    console.log("add the stupiddd part");
    
    // Use .value to update the ref
    // Access inventoryFields (computed) directly or via .value
    formFields.value = inventoryFields.value; 
    
    // formOpen is a ref, so use .value
    formOpen.value = true; 
  }
};

const formOpen = ref(false);

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

const formFields = ref([]);

const handleSave = (newData) => {
  console.log("Saving to Database:", newData);
  api.createPart(newData);
  formOpen.value = false;
};

const closeForm = () => {
  formOpen.value = false;
};
</script>

<template>
  <div class="app-wrapper">
     <SideBar 
      v-model="activeFilters" 
      :config="sidebarConfig" 
    />
    <main v-if="!formOpen">
      <NavBar />
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
        title="Jaunas detaļas reģistrācija"
        :fields="formFields"
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