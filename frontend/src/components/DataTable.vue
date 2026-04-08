<script setup>
import { ref, computed } from 'vue';

// Tabulas dati un pogas
const props = defineProps({
  columns: { type: Array, required: true },
  data: { type: Array, required: true },
  filters: { type: Object, default: () => ({}) },
  rowActions: { type: Array, default: () => [] },
  globalActions: { type: Array, default: () => [] }
});

const emit = defineEmits(['action', 'globalAction']);

// Kārtošanas secība
const sortStack = ref([]);

const handleSort = (fieldId) => {
  const existingIdx = sortStack.value.findIndex(s => s.fieldId === fieldId);
  
  if (existingIdx === -1) {
    sortStack.value.push({ fieldId, direction: 'asc' });

  } else {
    const current = sortStack.value[existingIdx];

    if (current.direction === 'asc') {
      current.direction = 'desc';

    } else {
      sortStack.value.splice(existingIdx, 1);
    }
  }
};

// Datu filtrēšana
const processedData = computed(() => {
  let result = [...props.data];

  result = result.filter(item => {
    return Object.keys(props.filters).every(key => {
      const filterVal = props.filters[key];

      if (!filterVal) return true;
      if (!(key in item)) return true; 

      return String(item[key]).toLowerCase().includes(String(filterVal).toLowerCase());
    });
  });

  // Pati kārtošana
  if (sortStack.value.length > 0) {
    result.sort((a, b) => {

      // Katrai kārtošanas secībai
      for (let rule of sortStack.value) {
        const valA = a[rule.fieldId];
        const valB = b[rule.fieldId];
        if (valA === valB) continue;

        const comparison = typeof valA === 'number' 
          ? valA - valB 
          : String(valA).localeCompare(String(valB));
        
        return rule.direction === 'asc' ? comparison : -comparison;
      }
      return 0;
    });
  }

  return result;
});

const getSortInfo = (id) => sortStack.value.find(s => s.fieldId === id);
const getSortPriority = (id) => sortStack.value.findIndex(s => s.fieldId === id) + 1;
</script>

<template>
  <div class="table-container">
    <div class="table-controls">
      <div class="stats-badge">Kopā: {{ processedData.length }} ieraksti</div>
      <div class="global-actions">
        <button 
          v-for="action in globalActions" 
          :key="action.label"
          class="btn-primary-action"
          @click="emit('globalAction', action.id)"
        >
          {{ action.label }}
        </button>
      </div>
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th 
            v-for="col in columns" 
            :key="col.id" 
            class="table-header"
            @click="handleSort(col.id)"
          >
            {{ col.label }}
            <span v-if="getSortInfo(col.id)" class="sort-indicator">
              {{ getSortInfo(col.id).direction === 'asc' ? ' ↑' : ' ↓' }}
            </span>
            <span v-if="getSortPriority(col.id) > 0" class="priority-badge">
              {{ getSortPriority(col.id) }}
            </span>
          </th>
          <th v-if="rowActions.length" class="table-header">Darbība</th>
        </tr>
      </thead>
      
      <tbody>
        <tr v-for="(item, rowIdx) in processedData" :key="rowIdx" class="row-item">
          <td v-for="(col, colIdx) in columns" :key="col.id">
            <div v-if="colIdx === 0" class="accent-marker"></div>
            
            <slot :name="`col-${col.id}`" :value="item[col.id]" :item="item">
              {{ col.id === 'price' ? `${item[col.id].toFixed(2)} €` : item[col.id] }}
            </slot>
          </td>

          <td v-if="rowActions.length">
            <div class="action-cell">
              <button 
                v-for="action in rowActions" 
                :key="action.id"
                :class="['btn-action', action.class || 'btn-primary-action']"
                @click="emit('action', { action: action.id, item })"
              >
                {{ action.label }}
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-container { 
  width: 100%; 
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.table-header {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  text-align: left;
  padding-bottom: 12px;
  border-bottom: 1px solid #e2e8f0;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.table-header:hover { 
  color: #2563eb; 
}

.row-item {
 transition: background-color 0.2s; 
}

.row-item:hover {
 background-color: #eff6ff;
}

.row-item td {
  padding: 22px 0;
  font-size: 0.95rem;
  position: relative;
}

.accent-marker {
  position: absolute;
  left: 0;
  top: 100%;
  transform: translateY(-50%);
  width: 70%;
  height: 4px;
  background-color: #2563eb;
  opacity: 0.4;
  border-radius: 0 4px 4px 0;
}

.btn-primary-action {
  padding: 8px 16px;
  border: 1.5px solid #2563eb;
  color: #2563eb;
  font-weight: 700;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  font-size: 0.85rem;
}

.btn-primary-action:hover {
  background: #2563eb;
  color: white;
}

.btn-danger {
  color: #ef4444;
  border-color: #ef4444; 
}
.btn-danger:hover { 
  background: #ef4444; 
  color: white;
}

.stats-badge {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.sort-indicator {
  margin-left: 4px;
  color: #2563eb;
}

.priority-badge {
  font-size: 0.65rem;
  background: #e2e8f0;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: 4px;
  vertical-align: middle;
}

.action-cell {
  display: flex;
  gap: 8px;
}
</style>