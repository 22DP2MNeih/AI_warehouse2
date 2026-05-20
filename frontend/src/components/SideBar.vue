<script setup>
import { ref } from 'vue';
import SideBarSliderInput from './SideBarSliderInput.vue';
import SideBarTextInput from './SideBarTextInput.vue';
import SideBarSearchInput from './SideBarSearchInput.vue';
import SideBarCheckBoxInput from './SideBarCheckBoxInput.vue';

const props = defineProps({
  title: { type: String, default: 'Meklēšana' },
  config: { type: Array, required: true },
  modelValue: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['update:modelValue']);

// Local state to manage drawer display on mobile viewports
const isOpen = ref(false);

const componentMap = {
  text: SideBarTextInput,
  search: SideBarSearchInput,
  slider: SideBarSliderInput,
  checkbox: SideBarCheckBoxInput
};

const updateFilter = (id, value) => {
  const newFilters = { ...props.modelValue, [id]: value };
  emit('update:modelValue', newFilters);
};
</script>

<template>
  <!-- Floating Mobile Trigger Button -->
  <button 
    class="mobile-trigger" 
    @click="isOpen = true" 
    aria-label="Atvērt filtrus"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
    </svg>
    <span>Filtri</span>
  </button>

  <!-- Dimmed Backdrop for Mobile Overlay Overlay View -->
  <div 
    class="sidebar-backdrop" 
    :class="{ 'is-visible': isOpen }" 
    @click="isOpen = false"
  ></div>

  <!-- Sidebar Container Layer -->
  <aside id="sidebar" :class="{ 'is-open': isOpen }">
    <div class="sidebar-header-wrapper">
      <div class="sidebar-section-header">{{ title }}</div>
      
      <!-- Close button built exclusively for mobile screen constraints -->
      <button 
        class="close-btn" 
        @click="isOpen = false" 
        aria-label="Aizvērt filtrus"
      >
        ✕
      </button>
    </div>

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
/* Ensure border-box sizing is applied within the sidebar context */
#sidebar,
#sidebar * {
  box-sizing: border-box;
}

/* Desktop Layout Base Layout Configurations */
#sidebar {
  width: 300px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  
  /* Vertical scrolling allowed, Horizontal scrolling explicitly banned */
  overflow-y: auto;
  overflow-x: hidden; 
  
  transition: transform 0.3s ease;
}

/* OPTIONAL: Hides the default ugly scrollbar for a cleaner look */
#sidebar::-webkit-scrollbar {
  width: 6px;
}
#sidebar::-webkit-scrollbar-track {
  background: transparent;
}
#sidebar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 3px;
}

.sidebar-header-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #eff6ff;
  margin-bottom: 16px;
  padding-right: 16px;
  width: 100%;
}

.sidebar-section-header {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #2563eb;
  padding: 24px 20px 8px 20px;
}

/* Isolates the inner area and breaks down sub-components */
.filter-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.field-group {
  padding: 0 20px 16px 20px;
  width: 100%;
}

/* Force deeply nested input/child components to stay in bounds */
.field-group > * {
  max-width: 100% !important;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 6px;
}

/* Hidden elements layout configurations on desktop viewports */
.mobile-trigger,
.sidebar-backdrop,
.close-btn {
  display: none;
}

/* Mobile Breaking Breakpoint Framework Rules (Max-width: 768px) */
@media (max-width: 768px) {
  
  /* Fixed/Floating Mobile Filter Action Trigger Target Asset */
  .mobile-trigger {
    display: flex;
    align-items: center;
    gap: 8px;
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 40;
    background: #2563eb;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.9rem;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
    cursor: pointer;
  }

  /* Transition backdrop viewport shade setup configurations */
  .sidebar-backdrop {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(15, 23, 42, 0.4);
    z-index: 49;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.3s ease;
  }

  .sidebar-backdrop.is-visible {
    opacity: 1;
    pointer-events: auto;
  }

  /* Redefining layout parameters into an overlay drawer element sliding from left side zone */
  #sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    /* Keeps the sidebar mobile drawer contained nicely */
    max-width: 85vw; 
    z-index: 50;
    border-right: none;
    box-shadow: 4px 0 25px -5px rgba(0, 0, 0, 0.1);
    
    /* Initially hide off-screen to the left side layer framework spatial limit */
    transform: translateX(-100%);
  }

  #sidebar.is-open {
    transform: translateX(0);
  }

  .sidebar-header-wrapper {
    padding-top: 12px;
  }

  .sidebar-section-header {
    padding-top: 16px;
  }

  /* Expose explicit close target interface node asset element control properties */
  .close-btn {
    display: block;
    background: transparent;
    border: none;
    font-size: 1.25rem;
    color: #64748b;
    cursor: pointer;
    padding: 8px;
    margin-top: 8px;
  }
}
</style>