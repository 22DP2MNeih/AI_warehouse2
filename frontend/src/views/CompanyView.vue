<script setup>
import { ref, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import SideBar from '../components/SideBar.vue';
import NavBar from '../components/NavBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';
import api from '../services/api';

// --- State Management ---
const authStore = useAuthStore();
const { user, userRole } = storeToRefs(authStore);

const employees = ref([]);
const warehouses = ref([]);
const loading = ref(false);
const error = ref(null);

const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});
const selectedEmployee = ref(null);
const selectedWarehouse = ref(null);
const actionType = ref(""); // "approve", "edit", "add-warehouse", "edit-warehouse"
 
const isEmployeesCollapsed = ref(false);
const isEmployeeRequestsCollapsed = ref(false);
const isWarehousesCollapsed = ref(false);

const userMeta = computed(() => {
  return {
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});

const isCeo = computed(() => userRole.value === 'CEO');

const companyName = computed(() => {
  return user.value?.company_name || 'Mani Uzņēmuma Dati';
});

// --- Table and Sidebar Configs ---
const activeCols = [
  { id: 'username', label: 'E-pasts' },
  { id: 'role', label: 'Loma' },
  { id: 'warehouse_name', label: 'Noliktava' }
];

const pendingCols = [
  { id: 'username', label: 'E-pasts' },
  { id: 'role', label: 'Pieprasītā loma' }
];

const warehouseCols = [
  { id: 'name', label: 'Noliktava' },
  { id: 'address', label: 'Adrese' },
  { id: 'country_code', label: 'Valsts kods' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt darbinieku' }
];

const activeFilters = ref({
  search: ''
});

const roleLabelMap = {
  'CEO': 'Uzņēmuma vadītājs (CEO)',
  'WAREHOUSE_MANAGER': 'Noliktavas vadītājs',
  'MECHANIC': 'Mehāniķis',
  'ADMIN': 'Administrators'
};

const activeRowActions = [
  { id: 'edit', label: 'Rediģēt', class: 'btn-primary-action' },
  { id: 'delete', label: 'Noņemt', class: 'btn-danger' }
];

const pendingRowActions = [
  { id: 'approve', label: 'Apstiprināt', class: 'btn-primary-action' },
  { id: 'reject', label: 'Noraidīt', class: 'btn-danger' }
];

const warehouseRowActions = [
  { id: 'edit-warehouse', label: 'Rediģēt', class: 'btn-primary-action' },
  { id: 'delete-warehouse', label: 'Dzēst', class: 'btn-danger' }
];

// --- Authorization Computed Properties ---
const canManageWarehouses = computed(() => {
  return ['ADMIN', 'CEO', 'WAREHOUSE_MANAGER'].includes(userRole.value);
});

// --- Form Blueprints ---
const approveFields = computed(() => [
  { id: 'employee_name', type: 'text', label: 'Darbinieka e-pasts', disabled: true },
  { 
    id: 'warehouse_id', 
    type: 'select', 
    label: 'Piešķirt sākuma noliktavu', 
    options: warehouses.value.map(w => ({
      label: w.name,      
      key: w.id          
    })),
    required: true 
  }
]);

const editFields = computed(() => [
  { id: 'employee_name', type: 'text', label: 'Darbinieka e-pasts', disabled: true },
  { 
    id: 'role', 
    type: 'select', 
    label: 'Loma uzņēmumā', 
    options: [
      { key: 'CEO', label: 'Uzņēmuma vadītājs (CEO)' },
      { key: 'WAREHOUSE_MANAGER', label: 'Noliktavas vadītājs' },
      { key: 'MECHANIC', label: 'Mehāniķis' }
    ],
    required: true 
  },
  { 
    id: 'warehouse_id', 
    type: 'select', 
    label: 'Mainīt noliktavu', 
    options: warehouses.value.map(w => ({
      label: w.name,      
      key: w.id          
    })),
    required: true 
  }
]);

const warehouseFields = computed(() => [
  { id: 'name', type: 'text', label: 'Noliktavas nosaukums', required: true },
  { id: 'address', type: 'textarea', label: 'Adrese', required: false, fullWidth: true },
  { 
    id: 'country_code', 
    type: 'select', 
    label: 'Valsts', 
    placeholder: 'Izvēlieties valsti...',
    options: [
      { key: 'LV', label: 'Latvija (LV)' },
      { key: 'LT', label: 'Lietuva (LT)' },
      { key: 'EE', label: 'Igaunija (EE)' },
      { key: 'DE', label: 'Vācija (DE)' },
      { key: 'PL', label: 'Polija (PL)' },
      { key: 'FI', label: 'Somija (FI)' },
      { key: 'SE', label: 'Zviedrija (SE)' },
      { key: 'GB', label: 'Lielbritānija (GB)' },
      { key: 'US', label: 'ASV (US)' },
      { key: 'FR', label: 'Francija (FR)' },
      { key: 'IT', label: 'Itālija (IT)' },
      { key: 'ES', label: 'Spānija (ES)' },
      { key: 'NL', label: 'Nīderlande (NL)' },
      { key: 'OT', label: 'Cita valsts (OT)' }
    ],
    required: true
  }
]);

// --- Fetch Data ---
const fetchCompanyData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const [usersRes, warehouseRes] = await Promise.all([
      api.getCompanyUsers(),
      api.getWarehouses()
    ]);
    employees.value = usersRes.data;
    warehouses.value = warehouseRes.data;
  } catch (err) {
    console.error("Kļūda ielādējot datus:", err);
    error.value = "Neizdevās ielādēt uzņēmuma datus.";
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchCompanyData();
});

// --- Filtering Lists ---
const filteredActive = computed(() => {
  const list = employees.value.filter(e => e.approved === true);
  const searchLower = activeFilters.value.search?.toLowerCase() || '';
  if (!searchLower) return list;
  return list.filter(e => 
    e.username.toLowerCase().includes(searchLower) ||
    (roleLabelMap[e.role] || e.role).toLowerCase().includes(searchLower) ||
    (e.warehouse_name || '').toLowerCase().includes(searchLower)
  );
});

const filteredPending = computed(() => {
  const list = employees.value.filter(e => e.approved === false);
  const searchLower = activeFilters.value.search?.toLowerCase() || '';
  if (!searchLower) return list;
  return list.filter(e => 
    e.username.toLowerCase().includes(searchLower) ||
    (roleLabelMap[e.role] || e.role).toLowerCase().includes(searchLower)
  );
});

// --- Actions Handlers ---
const handleActiveAction = async ({ action, item }) => {
  if (action === 'edit') {
    actionType.value = "edit";
    selectedEmployee.value = item;
    formTitle.value = "Rediģēt darbinieku";
    formFields.value = editFields.value;
    formData.value = {
      employee_name: item.username,
      role: item.role,
      warehouse_id: item.warehouse || ''
    };
    formOpen.value = true;
  } else if (action === 'delete') {
    if (confirm(`Vai tiešām vēlaties noņemt darbinieku ${item.username} no uzņēmuma?`)) {
      try {
        await api.deleteUser(item.id);
        await fetchCompanyData();
        alert("Darbinieks veiksmīgi noņemts.");
      } catch (err) {
        console.error(err);
        alert("Kļūda noņemot darbinieku.");
      }
    }
  }
};

const handlePendingAction = async ({ action, item }) => {
  if (action === 'approve') {
    if (warehouses.value.length === 0) {
      alert("Lūdzu, vispirms izveidojiet vismaz vienu noliktavu, lai varētu apstiprināt darbiniekus.");
      return;
    }
    actionType.value = "approve";
    selectedEmployee.value = item;
    formTitle.value = "Apstiprināt darbinieku";
    formFields.value = approveFields.value;
    formData.value = {
      employee_name: item.username,
      warehouse_id: warehouses.value[0]?.id || ''
    };
    formOpen.value = true;
  } else if (action === 'reject') {
    if (confirm(`Vai tiešām vēlaties noraidīt darbinieka ${item.username} pieteikumu?`)) {
      try {
        await api.deleteUser(item.id);
        await fetchCompanyData();
        alert("Pieteikums noraidīts.");
      } catch (err) {
        console.error(err);
        alert("Kļūda noraidot pieteikumu.");
      }
    }
  }
};

const handleWarehouseGlobalAction = (action) => {
  if (action === 'add-warehouse') {
    actionType.value = "add-warehouse";
    formTitle.value = "Pievienot noliktavu";
    formFields.value = warehouseFields.value;
    formData.value = {
      name: '',
      address: '',
      country_code: 'LV'
    };
    formOpen.value = true;
  }
};

const handleWarehouseAction = async ({ action, item }) => {
  if (action === 'edit-warehouse') {
    actionType.value = "edit-warehouse";
    selectedWarehouse.value = item;
    formTitle.value = "Rediģēt noliktavu";
    formFields.value = warehouseFields.value;
    formData.value = {
      name: item.name,
      address: item.address,
      country_code: item.country_code || 'LV'
    };
    formOpen.value = true;
  } else if (action === 'delete-warehouse') {
    if (confirm(`Vai tiešām vēlaties dzēst noliktavu ${item.name}?`)) {
      try {
        await api.deleteWarehouse(item.id);
        await fetchCompanyData();
        alert("Noliktava veiksmīgi dzēsta.");
      } catch (err) {
        console.error(err);
        alert("Kļūda dzēšot noliktavu.");
      }
    }
  }
};

const handleSave = async (newData) => {
  try {
    if (actionType.value === 'approve') {
      await api.approveUser(selectedEmployee.value.id, newData.warehouse_id);
      alert("Darbinieks veiksmīgi apstiprināts un pievienots uzņēmumam!");
    } else if (actionType.value === 'edit') {
      const updatePayload = {
        role: newData.role,
        warehouse: newData.warehouse_id
      };
      await api.updateUser(selectedEmployee.value.id, updatePayload);
      alert("Darbinieka loma un noliktava veiksmīgi mainīta!");
    } else if (actionType.value === 'add-warehouse') {
      await api.createWarehouse(newData);
      alert("Noliktava veiksmīgi izveidota!");
    } else if (actionType.value === 'edit-warehouse') {
      await api.updateWarehouse(selectedWarehouse.value.id, newData);
      alert("Noliktavas dati veiksmīgi saglabāti!");
    }
    formOpen.value = false;
    await fetchCompanyData();
  } catch (err) {
    console.error(err);
    alert("Kļūda saglabājot izmaiņas.");
  }
};
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="company" />
    
    <div class="content-body">
      <SideBar v-model="activeFilters" :config="sidebarConfig" title="Meklēšana" />

      <main class="main-content">
        <template v-if="!formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">Uzņēmuma Pārvaldība</h1>
              <p class="view-subtitle">{{ companyName }} — Darbinieku un noliktavu pārvaldība</p>
            </div>
          </div>

          <!-- Active Employees Section -->
          <div class="section-container">
            <h2 class="section-title collapsible-header" @click="isEmployeesCollapsed = !isEmployeesCollapsed">
              <span class="toggle-arrow">{{ isEmployeesCollapsed ? '►' : '▼' }}</span>
              Aktīvie darbinieki
            </h2>
            <DataTable 
              v-show="!isEmployeesCollapsed"
              :columns="activeCols" 
              :data="filteredActive"
              :rowActions="isCeo ? activeRowActions : []"
              @action="handleActiveAction"
            >
              <template #col-role="{ value }">
                <span class="role-badge" :class="value.toLowerCase()">
                  {{ roleLabelMap[value] || value }}
                </span>
              </template>
            </DataTable>
          </div>

          <!-- Pending Join Requests Section (Only shown if user is CEO) -->
          <div v-if="isCeo" class="section-container">
            <h2 class="section-title collapsible-header" @click="isEmployeeRequestsCollapsed = !isEmployeeRequestsCollapsed">
              <span class="toggle-arrow">{{ isEmployeeRequestsCollapsed ? '►' : '▼' }}</span>
              Reģistrācijas pieteikumi 
              <span v-if="filteredPending.length > 0" class="pending-count-badge">
                {{ filteredPending.length }}
              </span>
            </h2>
            
            <div v-if="filteredPending.length === 0" v-show="!isEmployeeRequestsCollapsed" class="no-pending-msg">
              Nav jaunu reģistrācijas pieteikumu.
            </div>
            
            <DataTable 
              v-else
              v-show="!isEmployeeRequestsCollapsed"
              :columns="pendingCols" 
              :data="filteredPending"
              :rowActions="pendingRowActions"
              @action="handlePendingAction"
            >
              <template #col-role="{ value }">
                <span class="role-badge" :class="value.toLowerCase()">
                  {{ roleLabelMap[value] || value }}
                </span>
              </template>
            </DataTable>
          </div>

          <!-- Warehouses Section -->
          <div class="section-container">
            <div class="section-header-row">
              <h2 class="section-title collapsible-header" @click="isWarehousesCollapsed = !isWarehousesCollapsed">
                <span class="toggle-arrow">{{ isWarehousesCollapsed ? '►' : '▼' }}</span>
                Uzņēmuma Noliktavas
              </h2>
              <button v-if="canManageWarehouses" class="btn-primary-action btn-add-warehouse" @click="handleWarehouseGlobalAction('add-warehouse')">
                + Pievienot noliktavu
              </button>
            </div>
            
            <div v-show="!isWarehousesCollapsed">
              <div v-if="warehouses.length === 0" class="no-pending-msg">
                Nav reģistrētu noliktavu. Pievienojiet pirmo!
              </div>
              
              <DataTable 
                v-show="!isWarehousesCollapsed"
                v-else
                :columns="warehouseCols" 
                :data="warehouses"
                :rowActions="canManageWarehouses ? warehouseRowActions : []"
                @action="handleWarehouseAction"
              >
                <template #col-country_code="{ value }">
                  <span class="country-badge">{{ value }}</span>
                </template>
              </DataTable>
            </div>
          </div>
        </template>

        <div v-else class="form-container">
          <DynamicForm 
            :title="formTitle"
            :fields="formFields"
            :initialData="formData"
            @submit="handleSave"
            @cancel="formOpen = false"
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
  gap: 2.5rem;
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

.section-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapsible-header {
  cursor: pointer;
  user-select: none;
  transition: color 0.15s ease;
}

.collapsible-header:hover {
  color: #0f172a;
}

.toggle-arrow {
  display: inline-block;
  width: 1rem;
  font-size: 0.85rem;
  color: #94a3b8;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header-row .section-title {
  margin-bottom: 0;
}

.btn-add-warehouse {
  padding: 8px 16px;
  font-weight: 600;
  border-radius: 8px;
}

.pending-count-badge {
  background-color: #ef4444;
  color: white;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 700;
}

.no-pending-msg {
  color: #64748b;
  font-size: 0.95rem;
  font-style: italic;
  padding: 1rem 0;
}

.role-badge {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
}

.role-badge.ceo {
  background-color: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}

.role-badge.warehouse_manager {
  background-color: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
}

.role-badge.mechanic {
  background-color: #fef3c7;
  color: #d97706;
  border: 1px solid #fde68a;
}

.country-badge {
  background-color: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  text-transform: uppercase;
}
 
.form-container {
  display: flex;
  justify-content: center;
  padding-top: 1rem;
}
</style>