<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useAuthStore } from '../stores/auth';
import api from '../services/api';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';

// --- State Management ---
const authStore = useAuthStore();
const { user, userRole } = storeToRefs(authStore);

const predictions = ref([]);
const companySettingsList = ref([]); // List of all company settings (for Admin)
const companySettings = ref(null);      // Active / selected company settings
const selectedCompanyId = ref(null);    // Track active company ID for filtering
const loading = ref(false);
const training = ref(false);
const trainingAll = ref(false);
const error = ref(null);

const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});

const userMeta = computed(() => {
  return {
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});

const isAdmin = computed(() => userRole.value === 'ADMIN');

// --- AI Configuration & Filters ---
const filters = ref({
  search: '',
  serviceLevel: 95.0,
  weighting: 'Exponential',
  priority: 'Cost-Optimized',
  thresholdTime: 30, // Days
  sortBy: 'threshold_gap'
});

// --- Configurations ---
const tableCols = [
  { id: 'name', label: 'Nosaukums' },
  { id: 'vin', label: 'VIN' },
  { id: 'sku', label: 'SKU' },
  { id: 'warehouse', label: 'Noliktava' },
  { id: 'currentStock', label: 'Pašlaik noliktavā' },
  { id: 'aiThreshold', label: 'MI Slieksnis' },
  { id: 'cv2', label: 'CV^2' },
  { id: 'adi', label: 'ADI' },
  { id: 'trend', label: 'Tendence' },
  { id: 'price', label: 'Cena' },
  { id: 'lastOrdered', label: 'Iepriekš pasūtīts' },
  { id: 'orderQty', label: 'Pasūtīt' }
];

// Admin configuration table columns
const adminCompanyCols = [
  { id: 'name', label: 'Uzņēmums' },
  { id: 'service_level', label: 'Servisa līmenis' },
  { id: 'prediction_period', label: 'Prognozes periods (Dienas)' },
  { id: 'ai_epochs', label: 'Cikli (Epochs)' },
  { id: 'ai_update_frequency', label: 'Atjaunināšana (Stundas)' }
];

const adminRowActions = [
  { id: 'edit', label: 'Rediģēt', class: 'btn-primary-action' },
  { id: 'train', label: 'Apmācīt', class: 'btn-train-row' }
];

const sidebarConfig = [
  { id: 'search', type: 'text', label: 'Meklēt detaļu' }
];

// --- Form Blueprints for Admin Editing ---
const companyEditFields = computed(() => [
  { id: 'company_name', type: 'text', label: 'Uzņēmuma nosaukums', disabled: true },
  { id: 'service_level', type: 'number', label: 'Servisa līmenis (%)', required: true, min: 90, max: 99.9, step: 0.1 },
  { id: 'prediction_period', type: 'number', label: 'Prognozes periods (Dienas)', required: true, min: 7, max: 90 },
  { id: 'ai_epochs', type: 'number', label: 'Apmācības cikli (Epochs)', required: true, min: 10, max: 1000 },
  { id: 'ai_update_frequency', type: 'number', label: 'Atjaunināšanas biežums (Stundas)', required: true, min: 1, max: 168 }
]);

// --- Fetch Settings and Predictions ---
const fetchSettingsAndPredictions = async () => {
  loading.value = true;
  error.value = null;
  try {
    const settingsRes = await api.getCompanySettings();
    companySettingsList.value = settingsRes.data;

    if (isAdmin.value) {
      if (companySettingsList.value.length > 0) {
        // Default to first company if none is active yet
        if (!selectedCompanyId.value) {
          selectedCompanyId.value = companySettingsList.value[0].id;
        }
        const active = companySettingsList.value.find(c => c.id === selectedCompanyId.value);
        if (active) {
          companySettings.value = active;
          filters.value.serviceLevel = parseFloat(active.service_level) * 100;
          filters.value.thresholdTime = active.prediction_period;
        }
        await fetchPredictionsOnly(selectedCompanyId.value);
      } else {
        predictions.value = [];
      }
    } else {
      if (settingsRes.data && settingsRes.data.length > 0) {
        companySettings.value = settingsRes.data[0];
        selectedCompanyId.value = companySettings.value.id;
        filters.value.serviceLevel = parseFloat(companySettings.value.service_level) * 100;
        filters.value.thresholdTime = companySettings.value.prediction_period;
      }
      await fetchPredictionsOnly(selectedCompanyId.value);
    }
  } catch (err) {
    console.error(err);
    error.value = "Kļūda ielādējot datus.";
  } finally {
    loading.value = false;
  }
};

const fetchPredictionsOnly = async (companyId = null) => {
  try {
    const predRes = await api.getAIRecommendations(companyId);
    predictions.value = predRes.data.map(item => ({
      id: item.stock_id,
      company_product_id: item.company_product_id,
      name: item.product_name,
      vin: item.vin,
      sku: item.sku || '-',
      warehouse: item.warehouse || '-',
      currentStock: item.current_quantity,
      aiThreshold: item.prediction_floor,
      cv2: item.cv2 !== undefined ? item.cv2 : 0.15,
      adi: item.adi !== undefined ? item.adi : 1.2,
      trend: item.trend || 'Stable',
      price: item.price || 0.0,
      lastOrdered: item.last_ordered || 'Nav pasūtīts',
      orderQty: 0
    }));
  } catch (err) {
    console.error(err);
    predictions.value = [];
  }
};

onMounted(() => {
  fetchSettingsAndPredictions();
});

// --- Selection Handler for Admin Companies ---
const selectCompany = async (company) => {
  selectedCompanyId.value = company.id;
  companySettings.value = company;
  filters.value.serviceLevel = parseFloat(company.service_level) * 100;
  filters.value.thresholdTime = company.prediction_period;
  loading.value = true;
  await fetchPredictionsOnly(company.id);
  loading.value = false;
};

// --- Local filtering to avoid DataTable.vue prop.filters bugs ---
const filteredPredictions = computed(() => {
  if (!predictions.value) return [];
  const searchLower = filters.value.search.toLowerCase();
  return predictions.value.filter(item => {
    return (
      !searchLower ||
      (item.name && item.name.toLowerCase().includes(searchLower)) ||
      (item.vin && item.vin.toLowerCase().includes(searchLower)) ||
      (item.sku && item.sku.toLowerCase().includes(searchLower)) ||
      (item.warehouse && item.warehouse.toLowerCase().includes(searchLower))
    );
  });
});

// --- Actions ---
const saveSettings = async () => {
  if (!companySettings.value) return;
  loading.value = true;
  error.value = null;
  try {
    const data = {
      service_level: (filters.value.serviceLevel / 100).toFixed(3),
      prediction_period: filters.value.thresholdTime
    };
    const res = await api.updateCompanySettings(companySettings.value.id, data);
    companySettings.value = res.data;
    
    // Refresh predictions with new parameters
    await fetchPredictionsOnly(selectedCompanyId.value);
    alert("Iestatījumi saglabāti un prognozes pārrēķinātas!");
    await fetchSettingsAndPredictions();
  } catch (err) {
    console.error(err);
    alert("Kļūda saglabājot iestatījumus.");
  } finally {
    loading.value = false;
  }
};

const trainModel = async () => {
  if (!companySettings.value) return;
  training.value = true;
  error.value = null;
  try {
    await api.trainAI(companySettings.value.id);
    await fetchPredictionsOnly(selectedCompanyId.value);
    alert(`MI Modelis priekš ${companySettings.value.name} veiksmīgi pārmācīts!`);
  } catch (err) {
    console.error(err);
    alert("Kļūda neironu tīkla apmācībā. Iespējams, nav pietiekami daudz vēsturisko datu (nepieciešami vismaz 5 pabeigti CONSUME pasūtījumi).");
  } finally {
    training.value = false;
  }
};

// --- Admin Table Action Handlers ---
const handleAdminAction = async ({ action, item }) => {
  if (action === 'edit') {
    formData.value = {
      company_name: item.name,
      service_level: Math.round(parseFloat(item.service_level) * 1000) / 10,
      prediction_period: item.prediction_period,
      ai_epochs: item.ai_epochs,
      ai_update_frequency: item.ai_update_frequency
    };
    selectedCompanyId.value = item.id;
    companySettings.value = item;
    formTitle.value = `Konfigurēt ${item.name} MI`;
    formFields.value = companyEditFields.value;
    formOpen.value = true;
  } else if (action === 'train') {
    selectedCompanyId.value = item.id;
    companySettings.value = item;
    await trainModel();
  }
};

const handleSaveAdminSettings = async (submittedData) => {
  loading.value = true;
  try {
    const patchData = {
      service_level: (submittedData.service_level / 100).toFixed(3),
      prediction_period: parseInt(submittedData.prediction_period),
      ai_epochs: parseInt(submittedData.ai_epochs),
      ai_update_frequency: parseInt(submittedData.ai_update_frequency)
    };
    await api.updateCompanySettings(selectedCompanyId.value, patchData);
    alert("Uzņēmuma MI parametri veiksmīgi atjaunināti!");
    formOpen.value = false;
    await fetchSettingsAndPredictions();
  } catch (err) {
    console.error(err);
    alert("Neizdevās saglabāt parametrus.");
  } finally {
    loading.value = false;
  }
};

const trainAllCompaniesGlobal = async () => {
  trainingAll.value = true;
  error.value = null;
  try {
    const res = await api.trainAllCompanies();
    alert(res.data?.status || "Visu uzņēmumu neironu tīkli veiksmīgi pārmācīti!");
    await fetchSettingsAndPredictions();
  } catch (err) {
    console.error(err);
    alert("Kļūda globālajā apmācībā.");
  } finally {
    trainingAll.value = false;
  }
};

const handleBulkOrder = async () => {
  const itemsToOrder = predictions.value.filter(p => p.orderQty > 0);
  if (itemsToOrder.length === 0) {
    alert("Lūdzu, ievadiet daudzumu vismaz vienai detaļai.");
    return;
  }
  
  loading.value = true;
  try {
    const orderPromises = itemsToOrder.map(item => {
      const apiData = {
        order_type: "PURCHASE",
        product_listing: item.company_product_id,
        quantity: item.orderQty,
        destination_external: "MI Pasūtījums"
      };
      return api.createOrder(apiData);
    });
    
    await Promise.all(orderPromises);
    
    itemsToOrder.forEach(item => {
      item.orderQty = 0;
    });
    
    alert(`Pasūtījumi veiksmīgi izveidoti priekš ${itemsToOrder.length} detaļām!`);
  } catch (err) {
    console.error(err);
    alert("Kļūda veidojot pasūtījumus. Lūdzu, pārbaudiet datus un mēģiniet vēlreiz.");
  } finally {
    loading.value = false;
  }
};

const handleCsvExport = () => {
  if (predictions.value.length === 0) return;
  
  const headers = ['Nosaukums', 'VIN', 'SKU', 'Noliktava', 'Pašlaik noliktavā', 'MI Slieksnis', 'CV^2', 'ADI', 'Tendence', 'Cena', 'Iepriekš pasūtīts'];
  const rows = predictions.value.map(p => [
    p.name,
    p.vin,
    p.sku,
    p.warehouse,
    p.currentStock,
    p.aiThreshold,
    p.cv2,
    p.adi,
    p.trend,
    p.price,
    p.lastOrdered
  ]);
  
  let csvContent = "data:text/csv;charset=utf-8,\uFEFF"; // Latvian UTF-8 representation
  csvContent += [headers.join(','), ...rows.map(e => e.map(val => `"${String(val).replace(/"/g, '""')}"`).join(','))].join('\n');
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", `MI_prognozes_${companySettings.value?.name || 'uznemums'}_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  
  link.click();
  document.body.removeChild(link);
};
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="ai_predictions" />
    
    <div class="content-body">
      <SideBar v-model="filters" :config="sidebarConfig" title="Meklēšana" />

      <main class="main-content">
        <template v-if="!formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">
                {{ isAdmin ? 'MI Sistēmas Administrēšana' : 'MI Inventāra Prognozes' }}
              </h1>
              <p class="view-subtitle">
                {{ isAdmin ? 'Pārvaldiet visu uzņēmumu neironu tīklu parametrus un apmācību.' : 'Automātiski aprēķinātie krājumu sliekšņi optimālai darbībai.' }}
              </p>
            </div>
            
            <div class="view-actions">
              <!-- Admin Global Retraining Trigger -->
              <button 
                v-if="isAdmin" 
                class="btn-train-all" 
                @click="trainAllCompaniesGlobal" 
                :disabled="trainingAll"
              >
                {{ trainingAll ? 'Apmāca visus...' : 'Apmācīt visus uzņēmumus' }}
              </button>

              <!-- Normal User Actions -->
              <template v-else>
                <button class="btn-save" @click="saveSettings" :disabled="loading">
                  {{ loading ? 'Saglabā...' : 'Saglabāt Iestatījumus' }}
                </button>
                <button class="btn-train" @click="trainModel" :disabled="training">
                  {{ training ? 'Apmāca...' : 'Apmācīt MI' }}
                </button>
              </template>
            </div>
          </div>

          <!-- Main Predictions Table -->
          <!-- <div class="section-container"> -->
            <h2 class="section-title">
              {{ isAdmin ? `Detaļu prognozes priekš: ${companySettings?.name || '-'}` : 'Krājumu analīze un sliekšņi' }}
            </h2>
            
            <DataTable 
              :columns="tableCols"
              :data="filteredPredictions"
              :globalActions="[
                { id: 'order', label: 'Veikt pasūtījumu' },
                { id: 'csv', label: 'Eksportēt datus CSV' }
              ]"
              @globalAction="(id) => id === 'order' ? handleBulkOrder() : (id === 'csv' ? handleCsvExport() : null)"
            >
              <template #col-currentStock="{ value, item }">
                <span :class="['stock-display', value < item.aiThreshold ? 'critical' : 'stable']">
                  {{ value }}
                </span>
              </template>

              <template #col-trend="{ value }">
                <span :class="['trend-icon', value.toLowerCase()]">
                  {{ value === 'Rising' ? '↗' : value === 'Falling' ? '↘' : '→' }} {{ value }}
                </span>
              </template>

              <template #col-orderQty="{ item }">
                <input 
                  type="number" 
                  v-model.number="item.orderQty" 
                  class="order-input"
                  min="0"
                />
              </template>
            </DataTable>
          <!-- </div> -->
        </template>

        <!-- Admin Editing form Container -->
        <div v-else class="form-container">
          <DynamicForm 
            :title="formTitle"
            :fields="formFields"
            :initialData="formData"
            @submit="handleSaveAdminSettings"
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

.view-actions {
  display: flex;
  gap: 1rem;
}

.btn-save {
  background-color: #0f172a;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.btn-save:hover {
  background-color: #1e293b;
  transform: translateY(-1px);
}

.btn-train {
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
.btn-train:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

.btn-train-all {
  background-color: #6366f1;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.15), 0 2px 4px -1px rgba(99, 102, 241, 0.08);
}
.btn-train-all:hover {
  background-color: #4f46e5;
  transform: translateY(-1px);
}

.section-container {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 20px;
}

.company-row {
  cursor: pointer;
  transition: background-color 0.15s ease;
}
.company-row:hover {
  background-color: #f8fafc;
}

.active-selected-row {
  background-color: #eff6ff !important;
}

.company-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selection-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: transparent;
}
.active-selected-row .selection-indicator {
  background-color: #2563eb;
  box-shadow: 0 0 8px #2563eb;
}

.action-cell {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.8rem;
  border-radius: 6px;
}

.btn-primary-action {
  background: #2563eb;
  color: white;
  border: none;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary-action:hover {
  background: #1d4ed8;
}

.btn-train-row {
  background: #10b981;
  color: white;
  border: none;
  font-weight: 600;
  cursor: pointer;
}
.btn-train-row:hover {
  background: #059669;
}

.stock-display {
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
}
.stock-display.critical {
  color: #ef4444;
}
.stock-display.stable {
  color: #1e293b;
}

.trend-icon.rising {
  color: #22c55e;
}

.trend-icon.falling {
  color: #ef4444;
}

.trend-icon.stable {
  color: #64748b;
}

.order-input {
  width: 70px;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 600;
  text-align: center;
  outline: none;
}
.order-input:focus {
  border-color: #2563eb;
  background: #eff6ff;
}

.form-container {
  background: white;
  padding: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}
</style>