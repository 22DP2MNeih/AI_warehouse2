<script setup>
import { ref, computed } from 'vue';
import FormFieldWrapper from '../components/FormFieldWrapper.vue';
import DynamicForm from '../components/DynamicForm.vue';


const loginFields = [
  { id: 'email', type: 'text', label: 'E-pasts', required: true },
  { id: 'password', type: 'text', label: 'Parole', required: true },
];
const registerFields = [
  { id: 'email', type: 'text', label: 'E-pasts', required: true },
  { id: 'password', type: 'text', label: 'Parole', required: true },
  { id: 'role', type: 'text', label: 'Loma', required: true },
];

const isLogin = ref(true);
const loginErrors = ref("");

const fields = computed(() => {
  return isLogin.value ? loginFields : registerFields;
});
const submitLabel = computed(() => {
  return isLogin.value ? "Login" : "Sign in";
});
const errorsExist = computed(() => {
  return loginErrors !== "";
});
const changeLabel = computed(() => {
  return isLogin.value ? "Ja tev nav konts izveido." : "Ja tev ir konts ielogojies";
});
const switchLogin = () => {
  isLogin.value = !isLogin.value;
};


const handleSave = (userInfo) => {
  if (isLogin) {
    console.log("Logging in", userInfo);
  } else {
    console.log("Registring", userInfo);
  }
};

const handleRegister = async () => {
    loading.value = true;
    error.value = null;
    try {
        await authStore.register(form.value);
        // After register, log them in automatically
        await authStore.login({
            username: form.value.username,
            password: form.value.password
        });
        router.push('/');
    } catch (err) {
        if (err.response && err.response.data) {
            // Handle validation errors
            const msgs = Object.values(err.response.data).flat();
            error.value = msgs.join(' ');
        } else {
            error.value = t.value('auth.regFailed');
        }
    } finally {
        loading.value = false;
    }
};

console.log(fields.value[0].id);

</script>

<template>
  <div class="app-wrapper">
    <main>
      <div class="form-wrapper">
        <div class="form-container">
          <div class="form-header">
            <h2 class="form-title">{{ title }}</h2>
            <div class="accent-line"></div>
          </div>

          <form @submit.prevent="handleSubmit" class="form-grid">
            <div v-for="field in fields" :key="field.id" :class="field.fullWidth ? 'col-span-2' : ''">
              <FormFieldWrapper :id="field.id" :label="field.label" :required="field.required">
                
                <input v-if="field.type === 'text' || field.type === 'number'"
                  :type="field.type"
                  v-model="fields[field.id]"
                  class="form-input"
                  :placeholder="field.placeholder"
                />

                <select v-else-if="field.type === 'select'" v-model="fields[field.id]" class="form-input">
                  <option value="" disabled>{{ field.placeholder || 'Izvēlieties...' }}</option>
                  <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
                </select>

                <textarea v-else-if="field.type === 'textarea'"
                  v-model="fields[field.id]"
                  class="form-input min-h-[100px]"
                ></textarea>
              </FormFieldWrapper>
            </div>

            <div class="form-actions col-span-2">
              <button type="submit" class="btn-primary-action" @click="handleRegister">{{ submitLabel }}</button>
              <a type="submit" class="" @click="switchLogin">{{ changeLabel }}</a>
              <div v-if="errorsExist" class="login-errors">{{ loginErrors }}</div>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
:root {
  --bg-color: #f8fafc;
  --primary-blue: #2563eb;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  font-family: 'Inter', sans-serif;
}

.app-wrapper {
  display: flex;
  min-height: 100vh;
  background-color: var(--bg-color);
}
/* 
.page-content {
  padding: 40px;
} */
.login-errors{
  justify-content: center;
  padding-top: 20px;
  color: darkred;
}
.form-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}

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