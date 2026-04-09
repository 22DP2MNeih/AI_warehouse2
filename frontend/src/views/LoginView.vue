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

const fields = computed(() => {
  return isLogin.value ? loginFields : registerFields;
});
const submitLabel = computed(() => {
  return isLogin.value ? "Login" : "Sign in";
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
</script>

<template>
  <div class="app-wrapper">
    <main>
      <div class="form-wrapper">
        <DynamicForm 
          title="Jauna pasūtījuma izveide"
          :fields="fields"
          submitLabel=submitLabel
          @submit="handleSave"
          @cancel="switchLogin"
        >
          <template #col-orderQty="{ item }">
            <input 
              type="number" 
              v-model.number="item.orderQty" 
              class="order-input"
              min="0"
            />
          </template>
        </DynamicForm>
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

.form-wrapper {
  display: flex;
  justify-content: center;
  padding-top: 20px;
}
</style>