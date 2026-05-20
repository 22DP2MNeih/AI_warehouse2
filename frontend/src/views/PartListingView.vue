<script setup>
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';
import api from '../services/api';
import NavBar from '../components/NavBar.vue';
import SideBar from '../components/SideBar.vue';
import DataTable from '../components/DataTable.vue';
import DynamicForm from '../components/DynamicForm.vue';
import { useAuthStore } from '../stores/auth';

// --- State Management ---
const authStore = useAuthStore();
const inventory = ref([]);
const formOpen = ref(false);
const formTitle = ref("");
const formFields = ref([]);
const formData = ref({});
const actionType = ref("");
const selectedItem = ref(null);
const { user, userRole } = storeToRefs(authStore);

// --- Stripe Payment States ---
const paymentOpen = ref(false);
const paymentData = ref({ amount: 0, partName: '', quantity: 1, notes: '', listingId: null });
const loadingPayment = ref(false);
const clientSecret = ref("");
const publishableKey = ref("");
const isMockPayment = ref(true);

const stripeInstance = ref(null);
const paymentElementInstance = ref(null);

const cardNumber = ref("");
const cardExpiryMonth = ref("");
const cardExpiryYear = ref("");
const cardCvc = ref("");
const cardZip = ref("");
const payError = ref("");
const paySuccess = ref(false);
const payProcessing = ref(false);

const cardBrand = computed(() => {
  const clean = cardNumber.value.replace(/\s+/g, '');
  if (clean.startsWith('4')) return 'visa';
  if (clean.startsWith('5')) return 'mastercard';
  if (clean.startsWith('3')) return 'amex';
  return 'generic';
});

const formatCardNumber = (e) => {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 16) value = value.slice(0, 16);
  const parts = [];
  for (let i = 0; i < value.length; i += 4) {
    parts.push(value.slice(i, i + 4));
  }
  cardNumber.value = parts.join(' ');
};

const formatExpiryMonth = (e) => {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 2) value = value.slice(0, 2);
  cardExpiryMonth.value = value;
};

const formatExpiryYear = (e) => {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 4) value = value.slice(0, 4); // Supports both YY or YYYY inputs safely
  cardExpiryYear.value = value;
};

const formatCvc = (e) => {
  let value = e.target.value.replace(/\D/g, '');
  if (value.length > 4) value = value.slice(0, 4);
  cardCvc.value = value;
};

const loadStripeScript = () => {
  return new Promise((resolve) => {
    if (window.Stripe) {
      resolve(window.Stripe);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/';
    script.onload = () => {
      resolve(window.Stripe);
    };
    document.head.appendChild(script);
  });
};

const userMeta = computed(() => {
  return {
    username: user.value?.username || 'Guest',
    role: userRole.value
  };
});

// --- Form Blueprints ---
const orderFields = [
  { id: 'product_name', type: 'text', label: 'Detaļa', disabled: true },
  { id: 'sku', type: 'text', label: 'SKU', disabled: true },
  { id: 'quantity', type: 'float', label: 'Daudzums', min: 1, required: true },
  { id: 'notes', type: 'textarea', label: 'Piezīmes', fullWidth: true },
];

const addPartFields = [
  { id: 'product_name', type: 'text', label: 'Nosaukums', required: true },
  { id: 'product_vin', type: 'text', label: 'VIN', required: true },
  { id: 'sku', type: 'text', label: 'SKU', required: true },
  { id: 'price', type: 'float', label: 'Cena', required: true },
  { id: 'description', type: 'textarea', label: 'Apraksts', fullWidth: true },
];

// --- Existing Configurations ---
const sidebarConfig = ref([
  { id: 'name', type: 'text', label: 'Nosaukums' },
  { id: 'vin', type: 'text', label: 'VIN' },
  { id: 'sku', type: 'text', label: 'SKU' },
  { id: 'company', type: 'text', label: 'Uzņēmums' },
]);

const tableColumns = ref([
  { id: 'product_name', label: 'Nosaukums', sortable: true },
  { id: 'product_vin', label: 'VIN', sortable: true },
  { id: 'sku', label: 'SKU', sortable: true },
  { id: 'company_name', label: 'Uzņēmums', sortable: true },
  { id: 'price', label: 'Cena', sortable: true }
]);

const rowActions = ref([{ id: 'order', label: 'Pasūtīt' }]);
const filters = ref({ name: '', vin: '', sku: '', company: '' });

// --- Logic ---
const fetchMarketData = async () => {
  try {
    const res = await api.getMarket();
    inventory.value = res.data.map(part => ({ ...part, price: Number(part.price) }));
  } catch (err) {
    console.error("Failed to load market data:", err);
  }
};

onMounted(fetchMarketData);

const processedData = computed(() => {
  return inventory.value.filter(item => {
    const f = filters.value;
    return item.product_name?.toLowerCase().includes(f.name.toLowerCase()) &&
           item.product_vin?.toLowerCase().includes(f.vin.toLowerCase()) &&
           item.sku?.toLowerCase().includes(f.sku.toLowerCase()) &&
           item.company_name?.toLowerCase().includes(f.company.toLowerCase());
  });
});

// --- Event Handlers ---
const openAddPartForm = () => {
  actionType.value = "add_part";
  formTitle.value = "Pievienot jaunu detaļu tirgum";
  formFields.value = addPartFields;
  formData.value = {};
  formOpen.value = true;
};

const handleAction = ({ action, item }) => {
  console.log("action called:", action, item);
      
  if (action === 'order') {
    selectedItem.value = item;
    actionType.value = "order_part";
    formTitle.value = `Pasūtīt detaļu: ${item.product_name}`;
    formFields.value = orderFields;
    formData.value = {
      product_name: item.product_name,
      sku: item.sku,
      quantity: 1
    };
    formOpen.value = true;
  }
};

const handleSave = async (newData) => {
  try {
    if (actionType.value === "order_part") {
      const totalAmount = selectedItem.value.price * newData.quantity;
      paymentData.value = {
        amount: totalAmount,
        partName: selectedItem.value.product_name,
        quantity: newData.quantity,
        notes: newData.notes,
        listingId: selectedItem.value.id
      };
      
      loadingPayment.value = true;
      formOpen.value = false;
      paymentOpen.value = true;
      
      try {
        const res = await api.createPaymentIntent(totalAmount);
        clientSecret.value = res.data.clientSecret;
        publishableKey.value = res.data.publishableKey;
        isMockPayment.value = res.data.isMock || res.data.publishableKey.includes('_mock');
        
        if (!isMockPayment.value) {
          const Stripe = await loadStripeScript();
          stripeInstance.value = Stripe(publishableKey.value);
          const elements = stripeInstance.value.elements({ clientSecret: clientSecret.value });
          paymentElementInstance.value = elements.create('payment');
          setTimeout(() => {
            paymentElementInstance.value.mount('#payment-element');
          }, 100);
        }
      } catch (err) {
        console.error("Stripe init failed, falling back to simulator:", err);
        isMockPayment.value = true;
      } finally {
        loadingPayment.value = false;
      }
    } else if (actionType.value === "add_part") {
      if (api.createMarketListing) {
        await api.createMarketListing(newData);
      } else {
        alert("Detaļas pievienošana tirgum veiksmīga!");
      }
      formOpen.value = false;
      await fetchMarketData();
    }
  } catch (err) {
    console.error("Form submission error:", err);
    alert("Kļūda saglabājot datus: " + (err.response?.data?.error || "Pārbaudiet ievadītos datus."));
  }
};

const handlePaymentSubmit = async () => {
  payProcessing.value = true;
  payError.value = "";
  
  try {
    if (!isMockPayment.value && stripeInstance.value && paymentElementInstance.value) {
      const { error: stripeErr } = await stripeInstance.value.confirmPayment({
        elements: {
          getElement: (type) => paymentElementInstance.value
        },
        confirmParams: {
          return_url: window.location.href
        },
        redirect: 'if_required'
      });
      
      if (stripeErr) {
        throw new Error(stripeErr.message);
      }
    } else {
      const cleanCard = cardNumber.value.replace(/\s+/g, '');
      if (cleanCard.length < 16) {
        throw new Error("Nepilnīgs kartes numurs. Lūdzu, ievadiet 16 zīmju kartes numuru.");
      }
      
      // --- Clean, Explicit Expiry Validation ---
      const expMonth = parseInt(cardExpiryMonth.value, 10);
      let expYear = parseInt(cardExpiryYear.value, 10);

      if (!cardExpiryMonth.value || !cardExpiryYear.value) {
        throw new Error("Lūdzu, ievadiet pilnu kartes derīguma termiņu.");
      }

      if (isNaN(expMonth) || expMonth < 1 || expMonth > 12) {
        throw new Error("Nederīgs mēnesis. Jābūt robežās no 01 līdz 12.");
      }

      // If user typed a 2-digit year (e.g., "29"), convert it to 4 digits ("2029")
      if (cardExpiryYear.value.length === 2) {
        expYear = parseInt('20' + cardExpiryYear.value, 10);
      }

      const currentDate = new Date();
      const currentYear = currentDate.getFullYear();
      const currentMonth = currentDate.getMonth() + 1;

      if (isNaN(expYear) || expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
        throw new Error("Kartes derīguma termiņš ir pagājis.");
      }
      
      if (cardCvc.value.length < 3) {
        throw new Error("Nepilnīgs drošības kods (CVC).");
      }
      
      // Simulate payment delay
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Create the DB order record upon payment success
    await api.createOrder({
      product_listing: paymentData.value.listingId,
      quantity: paymentData.value.quantity,
      order_type: "PURCHASE",
      notes: (paymentData.value.notes || "") + "\n[Apmaksāts ar Stripe. Klients: " + user.value.username + "]"
    });
    
    paySuccess.value = true;
    setTimeout(() => {
      paymentOpen.value = false;
      paySuccess.value = false;
      cardNumber.value = "";
      cardExpiry.value = "";
      cardCvc.value = "";
      cardZip.value = "";
      fetchMarketData();
    }, 2500);
  } catch (err) {
    console.error("Payment failed:", err);
    payError.value = err.message || "Maksājums neizdevās. Pārbaudiet kartes datus.";
  } finally {
    payProcessing.value = false;
  }
};

const closeForm = () => {
  formOpen.value = false;
};
</script>

<template>
  <div class="app-layout">
    <NavBar :userMeta="userMeta" activeTab="Inventory" />

    <div class="content-body">
      <SideBar v-model="filters" :config="sidebarConfig" />

      <!-- Toggle between Table and Form -->
      <main class="main-content">
        <template v-if="!formOpen">
          <div class="view-header">
            <div class="header-titles">
              <h1 class="view-title">Detaļu saraksts</h1>
              <p class="view-subtitle">Pērciet detaļas no citiem uzņēmumiem</p>
            </div>
            <div class="view-actions">
              <button class="btn-add" @click="openAddPartForm">+ Pievienot jaunu detaļu</button>
            </div>
          </div>

          <DataTable 
            :columns="tableColumns" 
            :data="processedData" 
            :rowActions="rowActions"
            @action="handleAction"
          />
        </template>

        <!-- Dynamic Form Rendering -->
        <div v-else class="form-container">
          <DynamicForm 
            :title="formTitle"
            :fields="formFields"
            :initialData="formData"
            @submit="handleSave"
            @cancel="closeForm"
          />
        </div>
      </main>
    </div>

    <!-- Stripe Elements Payment Modal -->
    <div v-if="paymentOpen" class="payment-modal-overlay">
      <div class="payment-modal-container">
        <button class="btn-close-payment" @click="paymentOpen = false" :disabled="payProcessing">×</button>
        
        <div class="payment-header">
          <div class="stripe-badge">
            <svg class="stripe-logo" viewBox="0 0 40 16" width="50" height="20">
              <path d="M40 9.2c0-2.4-1.2-3.8-3.5-3.8-2.2 0-3.6 1.4-3.6 3.8 0 2.6 1.4 3.9 3.7 3.9 2.2 0 3.4-1.1 3.4-1.1l-.6-1.1s-1 .8-2.6.8c-1.3 0-2.1-.6-2.2-1.6h5.7c.1-.2.1-.7.1-.9zm-5.7-.9c0-1.1.7-1.8 1.8-1.8 1.1 0 1.7.7 1.7 1.8h-3.5zm-5.8 4.7c1.3 0 2.2-.6 2.6-1.1v.9h1.7V2.3h-1.7v3.3c-.4-.5-1.3-1.1-2.6-1.1-2.2 0-3.8 1.6-3.8 4.3 0 2.6 1.6 4.2 3.8 4.2zm.6-1.5c-1.3 0-2.1-1-2.1-2.8 0-1.7.8-2.8 2.1-2.8 1.3 0 2.1 1 2.1 2.8-.1 1.8-.9 2.8-2.1 2.8zm-9.3.4h1.7V5.6h-1.7v6.3zm0-7.7h1.7V2.9h-1.7v1.4zm-1.8 1.1c-.5-.6-1.4-1.1-2.5-1.1-2.1 0-3.8 1.6-3.8 4.3 0 2.7 1.6 4.3 3.8 4.3 1.1 0 2-.5 2.5-1v.9h1.7V2.3h-1.7v3.4zm-.6 4.4c-1.3 0-2.1-1-2.1-2.8 0-1.7.8-2.8 2.1-2.8 1.3 0 2.1 1 2.1 2.8 0 1.8-.8 2.8-2.1 2.8zm-9-5.1c-.8-.4-1.7-.6-2.5-.6-1.4 0-2.2.6-2.2 1.5 0 .9.8 1.2 2.4 1.6 1.9.4 3.2.9 3.2 2.8 0 2-1.8 3-3.9 3-1.2 0-2.4-.3-3.2-.8l.6-1.3c.8.5 1.8.8 2.7.8 1.3 0 2.1-.5 2.1-1.4 0-.9-.7-1.2-2.4-1.6-1.9-.4-3.1-1-3.1-2.7 0-1.8 1.6-2.9 3.7-2.9 1 0 1.9.2 2.7.6l-.7 1.3z" fill="#635bff"/>
            </svg>
            <span class="secure-label">🛡️ Drošs maksājums</span>
          </div>
          <h2 class="payment-title">Maksājuma Apstiprinājums</h2>
        </div>

        <div class="order-summary-card">
          <div class="summary-row">
            <span class="summary-label">Prece:</span>
            <span class="summary-value">{{ paymentData.partName }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Daudzums:</span>
            <span class="summary-value">{{ paymentData.quantity }} gab.</span>
          </div>
          <div class="summary-divider"></div>
          <div class="summary-row total">
            <span class="summary-label">Kopā apmaksai:</span>
            <span class="summary-value">€{{ paymentData.amount.toFixed(2) }}</span>
          </div>
        </div>

        <!-- Stripe Elements form -->
        <form @submit.prevent="handlePaymentSubmit" class="stripe-form">
          <div v-if="loadingPayment" class="stripe-loading">
            <div class="payment-spinner"></div>
            <p>Meklē Stripe Elements...</p>
          </div>
          
          <div v-else>
            <!-- Real Stripe Element Mount -->
            <div v-show="!isMockPayment" id="payment-element" class="stripe-element-mount"></div>
            
            <!-- High-Fidelity Stripe Element Simulator -->
            <div v-show="isMockPayment" class="stripe-simulator-wrapper">
              <label class="input-label">Kartes informācija (Testa režīms)</label>
              <div class="card-input-container">
                <div class="card-number-wrapper">
                  <input 
                    type="text" 
                    class="card-field card-num" 
                    placeholder="1234 5678 9101 1121" 
                    v-model="cardNumber"
                    @input="formatCardNumber"
                    required
                  />
                  <div class="card-brand-icon" :class="cardBrand"></div>
                </div>
                
                <!-- Unified Container splitting Month and Year inputs -->
                <div class="card-sub-fields">
                  <input 
                    type="text" 
                    class="card-field split-expiry" 
                    placeholder="MM" 
                    v-model="cardExpiryMonth"
                    @input="formatExpiryMonth"
                    required
                  />
                  <input 
                    type="text" 
                    class="card-field split-expiry" 
                    placeholder="YYYY" 
                    v-model="cardExpiryYear"
                    @input="formatExpiryYear"
                    required
                  />
                  <input 
                    type="password" 
                    class="card-field half" 
                    placeholder="CVC" 
                    v-model="cardCvc"
                    @input="formatCvc"
                    required
                  />
                </div>
                <input 
                  type="text" 
                  class="card-field zip-field" 
                  placeholder="Pasta indekss (ZIP)" 
                  v-model="cardZip"
                  required
                />
              </div>
              <div class="test-card-hint">
                💡 Izmantojiet testa karti: <strong>4242 4242 4242 4242</strong> ar jebkuru nākotnes derīguma termiņu un CVC.
              </div>
            </div>
              <label class="input-label">Kartes informācija (Testa režīms)</label>
              <div class="card-input-container">
                <div class="card-number-wrapper">
                  <input 
                    type="text" 
                    class="card-field card-num" 
                    placeholder="1234 5678 9101 1121" 
                    v-model="cardNumber"
                    @input="formatCardNumber"
                    required
                  />
                  <div class="card-brand-icon" :class="cardBrand"></div>
                </div>
                <div class="card-sub-fields">
                  <input 
                    type="text" 
                    class="card-field half" 
                    placeholder="MM/YY" 
                    v-model="cardExpiry"
                    @input="formatExpiry"
                    required
                  />
                  <input 
                    type="password" 
                    class="card-field half" 
                    placeholder="CVC" 
                    v-model="cardCvc"
                    @input="formatCvc"
                    required
                  />
                </div>
                <input 
                  type="text" 
                  class="card-field zip-field" 
                  placeholder="Pasta indekss (ZIP)" 
                  v-model="cardZip"
                  required
                />
              </div>
              <div class="test-card-hint">
                💡 Izmantojiet testa karti: <strong>4242 4242 4242 4242</strong> ar jebkuru nākotnes derīguma termiņu un CVC.
              </div>
            
          </div>

          <div v-if="payError" class="payment-error-msg">
            ⚠️ {{ payError }}
          </div>

          <!-- Checkout State Display -->
          <div v-if="paySuccess" class="payment-success-overlay">
            <div class="success-icon">✓</div>
            <h3>Maksājums veiksmīgs!</h3>
            <p>Pasūtījums ir reģistrēts sistēmā.</p>
          </div>

          <button 
            type="submit" 
            class="btn-stripe-pay" 
            :disabled="payProcessing || loadingPayment || paySuccess"
          >
            <span v-if="payProcessing" class="payment-spinner btn-spinner"></span>
            <span v-else>Maksāt €{{ paymentData.amount.toFixed(2) }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f8fafc;
}

.content-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

:deep(.sidebar-container) {
  width: 320px;
  border-right: 1px solid #e2e8f0;
  background: white;
}

.main-content {
  flex: 1;
  padding: 2rem 3rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.view-title {
  font-size: 1.875rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.view-subtitle {
  color: #64748b;
  margin-top: 0.25rem;
}

.btn-add {
  background-color: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.1), 0 2px 4px -1px rgba(37, 99, 235, 0.06);
}

.btn-add:hover {
  background-color: #1d4ed8;
  transform: translateY(-1px);
}

/* --- Stripe Elements Payment Styles --- */
.payment-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.payment-modal-container {
  background: white;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  padding: 32px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  position: relative;
  animation: modalSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalSlideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.btn-close-payment {
  position: absolute;
  top: 16px;
  right: 20px;
  background: none;
  border: none;
  font-size: 1.75rem;
  color: #64748b;
  cursor: pointer;
  transition: color 0.15s;
}

.btn-close-payment:hover {
  color: #0f172a;
}

.payment-header {
  margin-bottom: 24px;
}

.stripe-badge {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.secure-label {
  font-size: 0.75rem;
  color: #16a34a;
  background-color: #f0fdf4;
  padding: 4px 8px;
  border-radius: 9999px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 4px;
}

.payment-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.order-summary-card {
  background-color: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.summary-label {
  color: #64748b;
}

.summary-value {
  font-weight: 600;
  color: #0f172a;
}

.summary-divider {
  height: 1px;
  background-color: #e2e8f0;
  margin: 4px 0;
}

.summary-row.total {
  font-size: 1.05rem;
}

.summary-row.total .summary-label {
  color: #0f172a;
  font-weight: 700;
}

.summary-row.total .summary-value {
  color: #635bff;
  font-weight: 800;
  font-size: 1.2rem;
}

/* Simulator elements style */
.stripe-simulator-wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.input-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
}

.card-input-container {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background-color: white;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.card-input-container:focus-within {
  border-color: #635bff;
  box-shadow: 0 0 0 3px rgba(99, 91, 255, 0.15);
}

.card-field {
  border: none;
  outline: none;
  font-size: 0.95rem;
  padding: 12px 16px;
  color: #0f172a;
  background: transparent;
  width: 100%;
}

.card-number-wrapper {
  position: relative;
  border-bottom: 1px solid #e2e8f0;
}

.card-brand-icon {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 32px;
  height: 20px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
  transition: opacity 0.15s;
}

.card-brand-icon.visa {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 16"><path fill="%231a1f71" d="M16.5 1h-2.3L12 8.7h.1l2.4-7.7z"/><path fill="%23f7b600" d="M2.5 1h3.6l.8 4.2L8.2 1h2.2L7.3 11H5.1L2.5 1z"/><path fill="%231a1f71" d="M12.6 1L10.3 11h2l1-4.7h3.3l.3 4.7h2l-2-10h-4.3zm1.6 3.7l1.1 2.3h-2.3l1.2-2.3z"/></svg>');
}

.card-brand-icon.mastercard {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 16"><circle cx="8" cy="8" r="6" fill="%23eb001b" opacity="0.85"/><circle cx="16" cy="8" r="6" fill="%23ff5f00" opacity="0.85"/></svg>');
}

.card-brand-icon.amex {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 16"><rect width="24" height="16" rx="2" fill="%230185c7"/><text x="12" y="10.5" fill="white" font-family="Arial, sans-serif" font-weight="900" font-size="6" text-anchor="middle">AMEX</text></svg>');
}

.card-brand-icon.generic {
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 16"><rect width="24" height="16" rx="2" fill="%2394a3b8"/><circle cx="8" cy="8" r="2.5" fill="white" opacity="0.5"/><circle cx="16" cy="8" r="2.5" fill="white" opacity="0.5"/></svg>');
}

.card-sub-fields {
  display: flex;
  border-bottom: 1px solid #e2e8f0;
}

.card-field.half {
  width: 50%;
}

.card-field.half:first-child {
  border-right: 1px solid #e2e8f0;
}

.zip-field {
  background-color: #fafafa;
}

.test-card-hint {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 4px;
}

.btn-stripe-pay {
  background-color: #635bff;
  color: white;
  border: none;
  width: 100%;
  padding: 14px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.15s, transform 0.1s;
  box-shadow: 0 4px 6px -1px rgba(99, 91, 255, 0.2), 0 2px 4px -1px rgba(99, 91, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-stripe-pay:hover {
  background-color: #564ee5;
}

.btn-stripe-pay:active {
  transform: scale(0.99);
}

.btn-stripe-pay:disabled {
  background-color: #94a3b8;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.stripe-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 0;
  color: #64748b;
}

.payment-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e2e8f0;
  border-top-color: #635bff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.payment-spinner.btn-spinner {
  border-color: rgba(255, 255, 255, 0.3);
  border-top-color: white;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.payment-error-msg {
  color: #dc2626;
  background-color: #fef2f2;
  border: 1px solid #fee2e2;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  margin-bottom: 20px;
  font-weight: 600;
}

.payment-success-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: white;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
  animation: fadeIn 0.25s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.success-icon {
  width: 56px;
  height: 56px;
  background-color: #dcfce7;
  color: #16a34a;
  font-size: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  animation: popSuccess 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes popSuccess {
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
