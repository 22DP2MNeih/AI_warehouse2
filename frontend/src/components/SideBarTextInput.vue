<template>
  <input 
    type="text" 
    class="sidebar-input" 
    placeholder="" 
    :value="modelValue"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>

<script setup>
defineProps(['modelValue']);
defineEmits(['update:modelValue']);
</script>

<style scoped>
.sidebar-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  outline: none;
}
.sidebar-input:focus { border-color: #2563eb; }
</style>