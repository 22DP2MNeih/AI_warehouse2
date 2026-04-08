<script setup>
import { ref } from 'vue';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';

const sidebarConfig = [
  { id: 'company_name', type: 'text', label: 'Kompānijas Nosaukums' },
  { id: 'location', type: 'text', label: 'Atrašanās vieta' },
  { id: 'postal_code', type: 'text', label: 'Pasta indekss' },
  { id: 'service_level', type: 'slider', label: 'Servisa Līmenis', modelValue: 97.8, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'weight', type: 'slider', label: 'Svērums', modelValue: 93.6, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'procurement_priorities', type: 'slider', label: 'Iegādes prioritātes', modelValue: 95.9, min: 90, max: 99.5, step: 0.1, unit: '%' },
];

const tableCols = [
  { id: 'name', label: 'Nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'warehouse', label: 'Noliktava'},
  { id: 'available', label: 'Pieejams'},
  { id: 'locCode', label: 'Novietojuma kods' },
  { id: 'desc', label: 'Apraksts' },
  { id: 'price', label: 'Cena'}
];

let inventory = [
  { name: "Bremžu kluči", vin: "VF312345678", sku: "BK-9901", warehouse: "Rīga-A", available: 12, locCode: "A-12-3", desc: "Priekšējie keramiskie", price: 45.50 },
  { name: "Eļļas filtrs", vin: "WBA998877", sku: "EF-002", warehouse: "Rīga-A", available: 45, locCode: "B-01-1", desc: "Sintētiskajai eļļai", price: 8.20 },
  { name: "Zobsiksna", vin: "TMB112233", sku: "ZS-554", warehouse: "Ogre-1", available: 3, locCode: "C-05-9", desc: "Pastiprinātā", price: 120.00 },
  { name: "Aizdedzes svece", vin: "UU1223344", sku: "AS-12", warehouse: "Rīga-A", available: 24, locCode: "A-02-1", desc: "Iridija", price: 15.00 },
  { name: "Gaisa filtrs", vin: "VF312345678", sku: "GF-77", warehouse: "Valmiera", available: 8, locCode: "V-09-2", desc: "Standarta", price: 12.50 },
  { name: "Amortizators", vin: "WBA998877", sku: "AM-100", warehouse: "Rīga-B", available: 4, locCode: "X-01-4", desc: "Gāzes, aizmugurējais", price: 85.00 }
];

const myRowActions = [
  { id: 'use_part', label: 'Izmantot detaļu' },
  { id: 'delete', label: 'Dzēst', class: 'btn-danger' }
];

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
  console.log(`Executing ${action} for`, item.name);
  if (action === 'delete') {
    // Logic for deleting
  }
};
const handleGlobalAction = ({ globalAction}) => {
  console.log(`Executing global ${globalAction}`)
  if (globalAction === 'add-part') {
    console.log("add the stupiddd part")
    isAdding = true;
  }
};

const isAdding = ref(false);

const inventoryFields = [
  { id: 'name', type: 'text', label: 'Detaļas Nosaukums', required: true },
  { id: 'sku', type: 'text', label: 'SKU Kods', required: true },
  { id: 'warehouse', type: 'select', label: 'Noliktava', options: ['Rīga-A', 'Ogre-1'], required: true },
  { id: 'price', type: 'number', label: 'Cena (€)' },
  { id: 'desc', type: 'textarea', label: 'Papildus Apraksts', fullWidth: true }
];

const handleSave = (newData) => {
  console.log("Saving to Database:", newData);
  isAdding.value = false;
};
</script>

<template>
  <div class="app-wrapper">
     <SideBar 
      v-model="activeFilters" 
      :config="sidebarConfig" 
    />
    <main v-if="!isAdding">
      <NavBar />
      <div class="page-content">
        <DataTable 
          :columns="tableCols" 
          :data="inventory"
          :rowActions="myRowActions"
          :globalActions="myGlobalActions"
          @action="handleAction"
          @globalAction="(id) => { console.log(`Executing global ${id}`); if (id === 'add-part') { console.log(`add the stupiddd part`); isAdding = true; }}"
        />
      </div>
    </main>
    <main v-else class="flex justify-center pt-10">
      <DynamicForm 
        title="Jaunas detaļas reģistrācija"
        :fields="inventoryFields"
        @submit="handleSave"
        @cancel="isAdding = false"
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