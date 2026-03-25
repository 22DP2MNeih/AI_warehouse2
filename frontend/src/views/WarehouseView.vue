<script setup>
import { ref } from 'vue';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';

const employees = ref([
  { name: "Jānis Kalniņš", role: "Vadītājs", status: "Aktīvs" },
  { name: "Mārīte Ozola", role: "Operators", status: "Atvaļinājumā" },
  { name: "Artūrs Liepa", role: "Loģistika", status: "Aktīvs" }
]);

const handleAddEmployee = () => {
  const name = prompt("Ievadiet vārdu:");
  if (name) {
    employees.value.push({ name, role: "Jauns darbinieks", status: "Aktīvs" });
  }
};

const sidebarConfig = [
  { id: 'company_name', type: 'text', label: 'Kompānijas Nosaukums' },
  { id: 'location', type: 'text', label: 'Atrašanās vieta' },
  { id: 'postal_code', type: 'text', label: 'Pasta indekss' },
  { id: 'service_level', type: 'slider', label: 'Servisa Līmenis', modelValue: 97.8, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'weight', type: 'slider', label: 'Svērums', modelValue: 93.6, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'procurement_priorities', type: 'slider', label: 'Iegādes prioritātes', modelValue: 95.9, min: 90, max: 99.5, step: 0.1, unit: '%' },
];

// const inventoryData = ref([
//   { name: "Bremžu kluči", vin: "VF312345678", price: 45.50, warehouse: "Rīga-A" },
// ]);
const tableCols = [
  { id: 'name', label: 'Nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'warehouse', label: 'Noliktava' },
  { id: 'available', label: 'Pieejams' },
  { id: 'locCode', label: 'Novietojuma kods' },
  { id: 'desc', label: 'Apraksts' },
  { id: 'price', label: 'Cena' }
];

let inventory = [
  { name: "Bremžu kluči", vin: "VF312345678", sku: "BK-9901", warehouse: "Rīga-A", available: 12, locCode: "A-12-3", desc: "Priekšējie keramiskie", price: 45.50 },
  { name: "Eļļas filtrs", vin: "WBA998877", sku: "EF-002", warehouse: "Rīga-A", available: 45, locCode: "B-01-1", desc: "Sintētiskajai eļļai", price: 8.20 },
  { name: "Zobsiksna", vin: "TMB112233", sku: "ZS-554", warehouse: "Ogre-1", available: 3, locCode: "C-05-9", desc: "Pastiprinātā", price: 120.00 },
  { name: "Aizdedzes svece", vin: "UU1223344", sku: "AS-12", warehouse: "Rīga-A", available: 24, locCode: "A-02-1", desc: "Iridija", price: 15.00 },
  { name: "Gaisa filtrs", vin: "VF312345678", sku: "GF-77", warehouse: "Valmiera", available: 8, locCode: "V-09-2", desc: "Standarta", price: 12.50 },
  { name: "Amortizators", vin: "WBA998877", sku: "AM-100", warehouse: "Rīga-B", available: 4, locCode: "X-01-4", desc: "Gāzes, aizmugurējais", price: 85.00 }
];

// const tableCols = [
//   { id: 'name', label: 'Nosaukums' },
//   { id: 'vin', label: 'VIN' },
//   { id: 'warehouse', label: 'Noliktava' },
//   { id: 'price', label: 'Cena' }
// ];

const myRowActions = [
  { id: 'use_part', label: 'Izmantot detaļu' },
  // { id: 'edit', label: 'Rediģēt' },
  { id: 'delete', label: 'Dzēst', class: 'btn-danger' }
];

const myGlobalActions = [
  { id: 'add-part', label: 'Pievienot detaļu' },
  { id: 'export', label: 'Eksportēt CSV' },
  { id: 'import', label: 'Importēt CSV' }
];

const handleAction = ({ action, item }) => {
  console.log(`Executing ${action} for`, item.name);
  if (action === 'delete') {
    // Logic for deleting
  }
};
</script>

<template>
  <div class="app-wrapper">
    <!-- <SideBar /> -->
     <SideBar 
      v-model="activeFilters" 
      :config="sidebarConfig" 
    />
    <main>
      <NavBar />
      <div class="page-content">
        <DataTable 
          :columns="tableCols" 
          :data="inventory"
          :rowActions="myRowActions"
          :globalActions="myGlobalActions"
          @action="handleAction"
          @globalAction="(id) => console.log('Global:', id)"
        />
      </div>
    </main>
  </div>
</template>

<style>
/* Global resets and variables */
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