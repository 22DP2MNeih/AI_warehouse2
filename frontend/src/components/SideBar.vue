<script setup>
import { computed } from 'vue';
import SideBarSliderInput from './SideBarSliderInput.vue';
import SideBarTextInput from './SideBarTextInput.vue';
import SideBarSearchInput from './SideBarSearchInput.vue';

const props = defineProps({
  title: { type: String, default: 'Meklēšana' },
  // configuration: Array of { type: 'text'|'sort'|'slider', id: string, label: string, options?: any }
  config: { type: Array, required: true },
  modelValue: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['update:modelValue']);

// Map strings to actual components
const componentMap = {
  text: SideBarTextInput,
  search: SideBarSearchInput,
  slider: SideBarSliderInput
};

const updateFilter = (id, value) => {
  const newFilters = { ...props.modelValue, [id]: value };
  emit('update:modelValue', newFilters);
};
</script>

<template>
  <aside id="sidebar">
    <div class="sidebar-section-header">{{ title }}</div>
    <div class="filter-container">
      <div v-for="field in config" :key="field.id" class="field-group">
        <label class="field-label">{{ field.label }}</label>
        
        <component 
          :is="componentMap[field.type]"
          v-bind="field"
          :modelValue="modelValue[field.id]"
          @update:modelValue="(val) => updateFilter(field.id, val)"
        />
      </div>
    </div>
  </aside>
</template>

<style scoped>
#sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow-y: auto;
}

.sidebar-section-header {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #2563eb;
  padding: 24px 20px 8px 20px;
  border-bottom: 2px solid #eff6ff;
  margin-bottom: 16px;
}

.field-group {
  padding: 0 20px 16px 20px;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 6px;
}
</style>