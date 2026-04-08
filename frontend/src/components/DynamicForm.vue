<script setup>
import { ref } from 'vue';
import FormFieldWrapper from './FormFieldWrapper.vue';

const props = defineProps({
  title: String,
  fields: Array, // [{ id: 'name', type: 'text', label: 'Nosaukums', required: true }]
  initialData: Object,
  submitLabel: { type: String, default: 'Saglabāt' }
});

const emit = defineEmits(['submit', 'cancel']);
const formData = ref({ ...props.initialData });
const errors = ref({});

// Izdara validāciju
const handleSubmit = () => {
  let valid = true;

  // Pārbauda vai lauki, kuri ir obligāti ir izpildīti
  props.fields.forEach(f => {
    if (f.required && !formData.value[f.id]) {
      errors.value[f.id] = 'Šis lauks ir obligāts';
      valid = false;
    }
  });

  if (valid) emit('submit', formData.value);
};
</script>

<template>
  <div class="form-container">
    <div class="form-header">
      <h2 class="form-title">{{ title }}</h2>
      <div class="accent-line"></div>
    </div>

    <form @submit.prevent="handleSubmit" class="form-grid">
      <div v-for="field in fields" :key="field.id" :class="field.fullWidth ? 'col-span-2' : ''">
        <FormFieldWrapper :id="field.id" :label="field.label" :required="field.required" :error="errors[field.id]">
          
          <input v-if="field.type === 'text' || field.type === 'number'"
            :type="field.type"
            v-model="formData[field.id]"
            class="form-input"
            :placeholder="field.placeholder"
          />

          <select v-else-if="field.type === 'select'" v-model="formData[field.id]" class="form-input">
            <option value="" disabled>{{ field.placeholder || 'Izvēlieties...' }}</option>
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>

          <textarea v-else-if="field.type === 'textarea'"
            v-model="formData[field.id]"
            class="form-input min-h-[100px]"
          ></textarea>
        </FormFieldWrapper>
      </div>

      <div class="form-actions col-span-2">
        <button type="button" class="btn-secondary" @click="emit('cancel')">Atcelt</button>
        <button type="submit" class="btn-primary-action">{{ submitLabel }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.form-container {
  background: white;
  padding: 40px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  max-width: 800px;
}

.form-header { margin-bottom: 32px; position: relative; }
.form-title { font-size: 1.5rem; font-weight: 700; color: #1e293b; }
.accent-line { 
  width: 40px; height: 3px; background: #2563eb; margin-top: 8px; border-radius: 2px;
}

.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px; }
.col-span-2 { grid-column: span 2; }

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #1e293b;
  transition: all 0.2s;
  outline: none;
}

.form-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 16px;
}

.btn-secondary {
  padding: 10px 20px;
  color: #64748b;
  font-weight: 600;
  cursor: pointer;
  background: transparent;
  border: none;
}

/* Reusing your btn-primary-action styles */
.btn-primary-action {
  padding: 10px 24px;
  border: 1.5px solid #2563eb;
  color: #2563eb;
  font-weight: 700;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
}
.btn-primary-action:hover { background: #2563eb; color: white; }
</style>