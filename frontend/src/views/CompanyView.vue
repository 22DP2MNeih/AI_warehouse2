<script setup>
import { ref } from 'vue';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import Table from '../components/TheTable.vue';

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

const handleDelete = (index) => {
  employees.value.splice(index, 1);
};

const activeFilters = ref({
  name: '',
  price: 0,
  sortBy: 'name'
});

const percentageFormatter = new Intl.NumberFormat('lv-LV', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const sidebarConfig = [
  { id: 'company_name', type: 'text', label: 'Kompānijas Nosaukums' },
  { id: 'location', type: 'text', label: 'Atrašanās vieta' },
  { id: 'postal_code', type: 'text', label: 'Pasta indekss' },
  { id: 'service_level', type: 'slider', label: 'Servisa Līmenis', modelValue: 97.8, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'weight', type: 'slider', label: 'Svērums', modelValue: 93.6, min: 90, max: 99.5, step: 0.1, unit: '%' },
  { id: 'procurement_priorities', type: 'slider', label: 'Iegādes prioritātes', modelValue: 95.9, min: 90, max: 99.5, step: 0.1, unit: '%' },
];
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
        <Table 
          title="Darbinieki" 
          :items="employees" 
          @add="handleAddEmployee"
          @delete="handleDelete"
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