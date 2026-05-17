<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import FormFieldWrapper from '../components/FormFieldWrapper.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';
import { useConfigStore } from '../stores/config';

const router = useRouter();
const authStore = useAuthStore();
const configStore = useConfigStore();
const t = computed(() => configStore.t);

const loginFields = [
  { id: 'email', type: 'email', label: 'E-pasts', required: true },
  { id: 'password', type: 'password', label: 'Parole', required: true },
];

const registerFields = computed(() => {
  const fieldsList = [
    { id: 'email', type: 'email', label: 'E-pasts', required: true },
    { id: 'password', type: 'password', label: 'Parole', required: true },
    { 
      id: 'role', 
      type: 'select', 
      label: 'Izvēlieties lomu', 
      required: true,
      placeholder: 'Izvēlieties savu lomu...',
      options: [
        { key: 'CEO', label: 'Uzņēmuma vadītājs (CEO)' },
        { key: 'WAREHOUSE_MANAGER', label: 'Noliktavas vadītājs' },
        { key: 'MECHANIC', label: 'Mehāniķis' }
      ]
    },
    { 
      id: 'company_name', 
      type: 'text', 
      label: formData.value.role === 'CEO' ? 'Jauna uzņēmuma nosaukums' : 'Uzņēmums, kuram vēlaties pievienoties', 
      required: true 
    },
    { 
      id: 'warehouse_name', 
      type: 'text', 
      label: 'Uzņēmuma noliktavas nosaukums', 
      required: true 
    }
  ];
  
  // if (formData.value.role === 'CEO') {
  //   fieldsList.push({
  //     id: 'warehouse_name',
  //     type: 'text',
  //     label: 'Galvenās noliktavas nosaukums (Nav obligāts)',
  //     required: false,
  //     placeholder: 'Galvenā Noliktava'
  //   });
  // }
  
  return fieldsList;
});

const loginRedirect = {
  'ADMIN': '/ai_predictions',
  'CEO': '/company',
  'WAREHOUSE_MANAGER': '/warehouse',
  'MECHANIC': '/warehouse',
}

const isLogin = ref(true);

const formData = ref({
  email: '',
  password: '',
  role: 'MECHANIC',
  company_name: '',
  warehouse_name: ''
});

const fields = computed(() => {
  return isLogin.value ? loginFields : registerFields.value;
});

const submitLabel = computed(() => {
  return isLogin.value ? "Pieteikties" : "Reģistrēties";
});

const changeLabel = computed(() => {
  return isLogin.value ? "Ja tev nav konts, izveido to šeit." : "Ja tev jau ir konts, ielogojies šeit.";
});

const switchLogin = () => {
  isLogin.value = !isLogin.value;
  error.value = null;
};

const errors = ref({});
const error = ref(null);

const handleRegister = async () => {
  let valid = true;
  errors.value = {};
  error.value = null;

  // Validate fields
  fields.value.forEach(field => {
    if (field.required && !formData.value[field.id]) {
      errors.value[field.id] = 'Šis lauks ir obligāts';
      valid = false;
    }
  });

  if (!valid) {
    error.value = "Lūdzu, aizpildiet visus obligātos laukus.";
    return;
  }

  try {
    if (!isLogin.value) {
      // Register Workflow
      const registerData = {
        email: formData.value.email,
        password: formData.value.password,
        role: formData.value.role,
        company_name: formData.value.company_name,
        // warehouse_name: formData.value.role === 'CEO' ? (formData.value.warehouse_name || 'Galvenā Noliktava') : ''
        warehouse_name: formData.value.warehouse_name
      };
      await authStore.register(registerData);
      
      // If employee, show a pending message instead of logging in automatically
      if (formData.value.role !== 'CEO') {
        alert("Reģistrācijas pieteikums nosūtīts! Lūdzu, gaidiet sava uzņēmuma CEO apstiprinājumu.");
        isLogin.value = true;
        formData.value.password = '';
        return;
      }
    }
    
    // Login Workflow
    await authStore.login({
      username: formData.value.email,
      password: formData.value.password
    });
    
    router.push(loginRedirect[authStore.userRole]);
  } catch (err) {
    console.error(err);
    if (err.response && err.response.data) {
      const data = err.response.data;
      if (typeof data === 'object') {
        const msgs = Object.entries(data).map(([key, val]) => {
          const fieldName = key === 'company_name' ? 'Uzņēmums' : (key === 'email' ? 'E-pasts' : key);
          const valMsg = Array.isArray(val) ? val[0] : val;
          // Clean JWT detail messages
          if (key === 'detail') return valMsg;
          return `${fieldName}: ${valMsg}`;
        });
        error.value = msgs.join(' ');
      } else {
        error.value = data;
      }
    } else {
      error.value = "Darbība neizdevās. Pārbaudiet ievadītos datus.";
    }
    alert(error.value);
  }
};
</script>

<template>
  <div class="app-wrapper">
    <main>
      <div class="form-wrapper">
        <div class="form-container">
          <div class="form-header">
            <h2 class="form-title">{{ submitLabel }}</h2>
            <div class="accent-line"></div>
          </div>
          
          <form @submit.prevent="handleRegister" class="form-grid">
            <div v-for="field in fields" :key="field.id" :class="field.fullWidth ? 'col-span-2' : ''">
              <FormFieldWrapper :id="field.id" :label="field.label" :required="field.required">
                
                <input v-if="field.type === 'password' || field.type === 'email' || field.type === 'text' || field.type === 'number'"
                  :type="field.type"
                  v-model="formData[field.id]"
                  class="form-input"
                  :placeholder="field.placeholder"
                />

                <select v-else-if="field.type === 'select'" v-model="formData[field.id]" class="form-input">
                  <option value="" disabled>{{ field.placeholder || 'Izvēlieties...' }}</option>
                  <option v-for="opt in field.options" :key="opt.key || opt" :value="opt.key || opt">
                    {{ opt.label || opt }}
                  </option>
                </select>

                <textarea v-else-if="field.type === 'textarea'"
                  v-model="formData[field.id]"
                  class="form-input min-h-[100px]"
                ></textarea>
              </FormFieldWrapper>
            </div>

            <div class="form-actions col-span-2">
              <button type="submit" class="btn-primary-action">{{ submitLabel }}</button>
              <a class="switch-link" @click="switchLogin">{{ changeLabel }}</a>
              <div v-if="error" class="login-errors">{{ error }}</div>
            </div>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-wrapper {
  display: flex;
  min-height: 100vh;
  background-color: #f8fafc;
  align-items: center;
  justify-content: center;
}

main {
  width: 100%;
}

.login-errors {
  width: 100%;
  text-align: center;
  padding-top: 20px;
  color: #dc2626;
  font-weight: 600;
  font-size: 0.9rem;
}

.form-wrapper {
  display: flex;
  justify-content: center;
  padding: 40px 20px;
}

.form-container {
  background: white;
  padding: 40px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  width: 100%;
  max-width: 550px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
}

.form-header { 
  margin-bottom: 32px; 
  position: relative; 
}

.form-title { 
  font-size: 1.75rem; 
  font-weight: 800; 
  color: #0f172a; 
  letter-spacing: -0.025em;
}

.accent-line { 
  width: 40px; 
  height: 4px; 
  background: #2563eb; 
  margin-top: 8px; 
  border-radius: 4px;
}

.form-grid { 
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  color: #0f172a;
  transition: all 0.2s;
  outline: none;
  background-color: #f8fafc;
}

.form-input:focus {
  border-color: #2563eb;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.switch-link {
  color: #2563eb;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: color 0.15s;
}

.switch-link:hover {
  color: #1d4ed8;
  text-decoration: underline;
}

.btn-primary-action {
  width: 100%;
  padding: 12px 24px;
  border: none;
  color: white;
  font-weight: 700;
  background: #2563eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1), 0 2px 4px -1px rgba(37, 99, 235, 0.06);
}

.btn-primary-action:hover { 
  background: #1d4ed8; 
  transform: translateY(-1px);
}
</style>