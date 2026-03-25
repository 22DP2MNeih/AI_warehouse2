<script setup>
import { reactive } from 'vue';

const company = reactive({
  name: 'SIA Mana Firma',
  address: 'Latvija Rīga',
  zip: 'LV-1001'
});

const params = reactive({
  serviceLevel: 97.5,
  weight: 92.7,
  priority: 94.5
});
</script>

<template>
  <aside>
    <div class="sidebar-section">
      <h2>Uzņēmums</h2>
      <div class="field">
        <label>Nosaukums</label>
        <input type="text" v-model="company.name">
      </div>
      <div class="field">
        <label>Adrese</label>
        <input type="text" v-model="company.address">
      </div>
      <div class="field">
        <label>Pasta indekss</label>
        <input type="text" v-model="company.zip">
      </div>
    </div>

    <div class="sidebar-section">
      <h2>MI parametri</h2>
      <div class="mi-param" v-for="(val, key) in params" :key="key">
        <span>{{ key === 'serviceLevel' ? 'Servisa līmenis' : key === 'weight' ? 'Svērums' : 'Iegādes prioritātes' }}</span>
        <input type="number" step="0.1" v-model="params[key]" style="width: 3rem">
        <input type="range" min="0" max="100" step="0.1" v-model="params[key]">
      </div>
    </div>
  </aside>
</template>

<style scoped>
aside {
  width: 300px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  padding: 40px 25px;
  display: flex;
  flex-direction: column;
  gap: 35px;
  z-index: 10;
}

.sidebar-section h2 {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 24px;
  color: #2563eb;
  border-bottom: 1.5px solid #2563eb;
  display: inline-block;
  padding-bottom: 4px;
}

.field {
  margin-bottom: 24px;
}

.field label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}

.field input[type="text"] {
  width: 100%;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  background: #fdfdfd;
}

.mi-param {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.mi-param span {
  flex: 1;
  font-size: 0.85rem;
  font-weight: 500;
}

input[type="range"] {
  width: 80px;
  accent-color: #2563eb;
}
</style>