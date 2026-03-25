<template>
  <div class="slider-wrapper">
    <div class="input-container">
      <input 
        type="range" 
        :min="min" 
        :max="max" 
        :step="step"
        :value="modelValue"
        @input="updateValue($event.target.value)"
      >

      <input 
        type="number" 
        class="val-display"
        :min="min" 
        :max="max" 
        :step="step"
        :value="modelValue"
        @input="updateValue($event.target.value)"
      >
      <span>{{ unit }}</span>
    </div>

    <p v-if="formatter">
      Formatted: {{ formatter.format(modelValue) }}
    </p>
  </div>
</template>

<script setup>
const props = defineProps({
  // modelValue: { type: [Number, String], default: 0 },
  modelValue: { type: Number, default: 0 },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 1000 },
  step: { type: Number, default: 1 },
  unit: { type: String, default: '' },
  formatter: { type: Object, default: null }
});

const emit = defineEmits(['update:modelValue']);

// Helper to ensure we emit numbers and stay within bounds
const updateValue = (val) => {
  let num = parseFloat(val);
  if (isNaN(num)) num = props.min;
  
  // Optional: Clamp values between min and max
  const clamped = Math.max(props.min, Math.min(props.max, num));
  emit('update:modelValue', clamped);
};
</script>

<style scoped>
</style>