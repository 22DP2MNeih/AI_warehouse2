<script setup>
import { ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const { user, userRole } = storeToRefs(authStore);
const userMeta = computed(() => {
  return {
    // Access the .value because these are now refs
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});
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
      <NavBar :userMeta="userMeta" activeTab="company"/>
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