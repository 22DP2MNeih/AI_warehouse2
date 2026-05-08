<script setup>
import { ref, onMounted, computed } from 'vue';
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
// const handleAction = ({ action, item }) => {
//   if (!item) {
//     console.log(`No item`);
//     return;
//   }
//   last_part.value = item;
//   console.log(item);
//   console.log(`Executing ${action} for`, item.product_name);
//   if (action === 'use_part') {
//     action_type.value = action;
//     formFields.value = consumeFields;
//     formData.value = {
//       part_name: item.product_name,
//       vin_input: item.vin
//     }
//     // Logic for deleting
//     formOpen.value = true; 
//   } else if (action === '') {
//   }
// };

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
// const transferFields = [
//   { id: 'part_name', type: 'text', label: 'Detaļas Nosaukums', disabled: true },
//   { id: 'vin_input', type: 'text', label: 'VIN Kods', disabled: true },
//   { id: 'from_warehouse', type: 'text', label: 'Noliktava no', disabled: true },
//   { 
//     id: 'to_warehouse', // Pro-tip: Changed to _id since you'll likely save the ID, not the name
//     type: 'select', 
//     label: 'Noliktava uz', 
//     // Map the raw data to Label/Value pairs
//     options: warehouses.value.map(w => ({
//       label: w.name,      // What the user sees in the dropdown
//       key: w.id         // What gets sent to the database
//     })),
//     required: true 
//   },
//   { id: 'quantity', type: 'float', label: 'Daudzums', min: 0, step: 0.001, required: true },
// ];
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

// const handleSave = (newData) => {
//   if (action_type.value === "add-part") {
//     console.log("Saving to Database:", newData);
//     api.createPart(newData);
//     formOpen.value = false;
//   } else if (action_type.value === "use_part") {
//     const apiData = {
//       order_type: "CONSUME",
//       vin: newData.vin_input,
//       product_listing: last_part.value.company_product,
//       quantity: newData.quantity,
//       destination_external: newData.used_on,
//       from_warehouse: ""
//     }
//     // Lookup the warehouse ID by name
//     const warehouse = warehouses.value.find(w => w.name === last_part.value.warehouse_name);
//     if (warehouse) {
//       apiData.from_warehouse = warehouse.id;
//     } else {
//       console.log("Warehouse not found for:");
//       console.error("Warehouse not found for:", last_part.value);
//     }
//     console.log("Saving to Database:", last_part.value, newData, apiData);
//     createAndCompleteOrder(apiData);
//     formOpen.value = false;
//   } else if (action_type.value === "use_part") {

//   }
// };
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