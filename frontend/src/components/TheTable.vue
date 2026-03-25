<script setup>
defineProps({
  title: String,
  items: Array
});

const emit = defineEmits(['add', 'delete', 'edit']);
</script>

<template>
  <section class="data-section">
    <div class="section-header">
      <h3>{{ title }} ▾</h3>
      <button class="add-btn" @click="emit('add')">+ Jauns</button>
    </div>
    
    <div class="list-header">
      <span>Vārds, Uzvārds</span>
      <span>Loma</span>
      <span>Statuss</span>
      <span style="text-align:right">Darbības</span>
    </div>

    <div v-for="(item, index) in items" :key="index" class="list-item">
      <div class="item-main">{{ item.name }}</div>
      <div class="item-sub">{{ item.role }}</div>
      <div :style="{ 
        fontSize: '0.75rem', 
        color: item.status === 'Aktīvs' ? '#22c55e' : '#eab308', 
        fontWeight: 'bold' 
      }">
        {{ item.status }}
      </div>
      <div class="actions">
        <button class="icon-btn" @click="emit('edit', index)">Rediģēt</button>
        <button class="icon-btn" @click="emit('delete', index)">Dzēst</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.data-section {
  flex: 1;
  min-width: 480px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.add-btn {
  background: none;
  border: 1.5px solid #2563eb;
  color: #2563eb;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
}

.list-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 150px;
  padding: 12px 0;
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
}

.list-item {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1fr 150px;
  padding: 22px 0;
  align-items: center;
  font-size: 0.9rem;
  position: relative;
  border-top: 1px solid #f1f5f9;
}

.item-main { font-weight: 600; }
.item-sub { color: #64748b; font-size: 0.85rem; }

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.icon-btn {
  padding: 4px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.75rem;
}

.icon-btn:hover {
  background: #1e293b;
  color: white;
}
</style>