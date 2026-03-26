<template>
  <div class="form-field">
    <label :for="id" class="field-label">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </label>
    <slot></slot>
    <p v-if="error" class="error-text">{{ error }}</p>
  </div>
</template>

<script setup>
defineProps(['id', 'label', 'required', 'error']);
</script>

<style scoped>
.form-field { margin-bottom: 24px; }
.field-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748b;
  margin-bottom: 8px;
  letter-spacing: 0.025em;
}
.required-mark { color: #ef4444; margin-left: 2px; }
.error-text { color: #ef4444; font-size: 0.75rem; margin-top: 4px; }
</style>