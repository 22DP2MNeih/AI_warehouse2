<script setup>
import { onMounted, ref } from 'vue';

const props = defineProps({
  userMeta: { type: Object, required: true },
});
console.log(props.userMeta);

const canvasRef = ref(null);
const containerRef = ref(null);
const themeLabel = ref(null);

const isDarkMode = ref(false);
// Reactive state for the responsive mobile menu visibility
const isMenuOpen = ref(false);

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value;
};

class ThemeVisualizer {
  constructor(canvasElement, containerElement, labelRef) {
    this.canvas = canvasElement;
    this.ctx = this.canvas.getContext('2d');
    this.container = containerElement;
    this.label = labelRef;

    this.size = 20;
    this.padding = 8;
    this.canvas.width = this.size + (this.padding * 2);
    this.canvas.height = this.size + (this.padding * 2);

    this.isDark = false;
    this.progress = 0;
    this.animationSpeed = 0.04;
    this.rayCount = 12;

    this.colors = {
      sun: { r: 255, g: 190, b: 0 },
      moon: { r: 148, g: 163, b: 184 },
      ray: { r: 255, g: 165, b: 0 }
    };

    this.init();
  }

  init() {
    this.container.addEventListener('click', () => this.toggle());
    this.draw();
  }

  toggle() {
    this.isDark = !this.isDark;
    document.documentElement.setAttribute('data-theme', this.isDark ? 'dark' : 'light');
    if (this.label.value) {
      this.label.value.innerText = this.isDark ? 'Dark Mode' : 'Light Mode';
    }
    this.animate();
  }

  animate() {
    const target = this.isDark ? 1 : 0;
    const diff = target - this.progress;

    if (Math.abs(diff) > 0.001) {
      this.progress += diff * this.animationSpeed;
      this.draw();
      requestAnimationFrame(() => this.animate());
    } else {
      this.progress = target;
      this.draw();
    }
  }

  lerpColor(c1, c2, t) {
    const r = Math.round(c1.r + (c2.r - c1.r) * t);
    const g = Math.round(c1.g + (c2.g - c1.g) * t);
    const b = Math.round(c1.b + (c2.b - c1.b) * t);
    return `rgb(${r}, ${g}, ${b})`;
  }

  draw() {
    const { ctx, canvas, size, progress } = this;
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const mainRadius = size / 3;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    const currentColor = this.lerpColor(this.colors.sun, this.colors.moon, progress);
    ctx.beginPath();
    ctx.arc(centerX, centerY, mainRadius, 0, Math.PI * 2);
    ctx.fillStyle = currentColor;
    ctx.fill();

    if (progress > 0.01) {
      const shadowOffset = (mainRadius * 1.5) * (1 - progress) + (mainRadius * 0.45);
      const shadowRadius = mainRadius * 0.95;
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath();
      ctx.arc(centerX + shadowOffset, centerY - (shadowOffset * 0.2), shadowRadius, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();

    if (progress < 0.95) {
      const rayOpacity = Math.max(0, 1 - (progress * 1.2));
      const rayLength = (size / 9.2) * (1 - progress);
      const innerDist = mainRadius + 6;

      ctx.save();
      ctx.strokeStyle = `rgba(${this.colors.ray.r}, ${this.colors.ray.g}, ${this.colors.ray.b}, ${rayOpacity})`;
      ctx.lineWidth = 2.5;
      ctx.lineCap = 'round';

      for (let i = 0; i < this.rayCount; i++) {
        const angle = (i * Math.PI * 2) / this.rayCount;
        const rotation = progress * 0.5;
        const x1 = centerX + Math.cos(angle + rotation) * innerDist;
        const y1 = centerY + Math.sin(angle + rotation) * innerDist;
        const x2 = centerX + Math.cos(angle + rotation) * (innerDist + rayLength);
        const y2 = centerY + Math.sin(angle + rotation) * (innerDist + rayLength);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
      ctx.restore();
    }
  }
}

onMounted(() => {
  if (canvasRef.value && containerRef.value) {
    new ThemeVisualizer(canvasRef.value, containerRef.value, themeLabel);
  }
});

const tabs = [
  {id: "parts", text: "Detaļu izvēlne", link: "/parts"}, 
  {id: "company", text: "Uzņēmums", link: "/company"},
  {id: "order", text: "Pasūtījumi", link: "/orders"},
  {id: "warehouse", text: "Noliktva", link: "/warehouse"},
  {id: "options", text: "Iestatījumi", link: "/options"},
  {id: "ai_predictions", text: "MI ieteikumi", link: "/ai_predictions"},
]
</script>

<template>
  <header>
    <!-- Brand / Logo space or placeholder to keep header structured on mobile -->
    <div class="header-brand">
      <strong>Sistēma</strong>
    </div>

    <!-- Burger Button Component -->
    <button 
      class="burger-btn" 
      :class="{ 'is-active': isMenuOpen }" 
      @click="toggleMenu"
      aria-label="Toggle navigation menu"
    >
      <span class="burger-line"></span>
      <span class="burger-line"></span>
      <span class="burger-line"></span>
    </button>

    <!-- Navigation Container (Responsive Drawer/Overlay) -->
    <div class="nav-container" :class="{ 'is-open': isMenuOpen }">
      <ul class="tabs">
        <li v-for="tab in tabs" :key="tab.id">
          <router-link :to="tab.link" @click="isMenuOpen = false">{{ tab.text }}</router-link>
        </li>
      </ul>

      <div class="header-tools">
        <div class="user-meta">
          <strong>{{ props.userMeta?.username }}</strong>
          <strong>{{ props.userMeta?.role }}</strong>
          <span class="logout">Iziet</span>
        </div>
        
        <div ref="containerRef" title="Toggle Dark/Light Mode" class="toggle-container-style">
          <canvas ref="canvasRef"></canvas>
        </div>
        <div class="label-text" ref="themeLabel" v-show="false">Light Mode</div>

        <div class="btn-sq">LV</div>
      </div>
    </div>
  </header>
</template>

<style scoped>
header {
  height: 90px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 0 40px;
  position: relative;
  z-index: 100;
}

.header-brand {
  align-self: center;
  margin-bottom: 12px;
  font-size: 1.1rem;
  color: #1e293b;
}

.nav-container {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: flex-end;
}

.tabs {
  display: flex;
  gap: 15px;
  list-style: none;
}

.tabs li a {
  padding: 12px 20px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  color: #64748b;
  display: block;
}

.tabs li a.active {
  color: #2563eb;
  font-weight: 700;
  position: relative;
}

.tabs li a.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: #2563eb;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 12px;
}

.toggle-container-style {
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
}

.label-text {
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.875rem;
  opacity: 0.7;
}

.user-meta { text-align: right; font-size: 0.85rem; }
.user-meta strong { display: block; }
.logout { color: #ef4444; font-weight: 600; cursor: pointer; margin-left: 8px; font-size: 0.75rem; }

.btn-sq {
  width: 40px;
  height: 40px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* Hidden by default on desktop viewports */
.burger-btn {
  display: none;
}

/* Mobile Layout Brakepoint (Max-width: 1024px) */
@media (max-width: 1024px) {
  header {
    align-items: center;
    padding: 0 20px;
    height: 70px;
  }

  .header-brand {
    margin-bottom: 0;
  }

  /* Expose the burger toggle button */
  .burger-btn {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: 24px;
    height: 18px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    z-index: 101;
  }

  .burger-line {
    width: 100%;
    height: 2px;
    background-color: #334155;
    transition: transform 0.3s ease, opacity 0.3s ease;
  }

  /* Morphing burger animations into an 'X' close pattern when active */
  .burger-btn.is-active .burger-line:nth-child(1) {
    transform: translateY(8px) rotate(45deg);
  }

  .burger-btn.is-active .burger-line:nth-child(2) {
    opacity: 0;
  }

  .burger-btn.is-active .burger-line:nth-child(3) {
    transform: translateY(-8px) rotate(-45deg);
  }

  /* Transform nav-container into a full drawer menu system over the screen area */
  .nav-container {
    position: absolute;
    top: 70px;
    left: 0;
    width: 100%;
    background: white;
    border-bottom: 1px solid #e2e8f0;
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    padding: 20px;
    gap: 25px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    
    /* Smooth slide-down display animation transitions */
    opacity: 0;
    transform: translateY(-10px);
    pointer-events: none;
    transition: opacity 0.25s ease, transform 0.25s ease;
  }

  .nav-container.is-open {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
  }

  .tabs {
    flex-direction: column;
    width: 100%;
    gap: 5px;
  }

  .tabs li {
    width: 100%;
  }

  .tabs li a {
    padding: 12px 10px;
    font-size: 1rem;
  }

  .tabs li a.active::after {
    bottom: unset;
    left: 0;
    top: 0;
    width: 4px;
    height: 100%;
  }

  .header-tools {
    width: 100%;
    justify-content: space-between;
    margin-bottom: 0;
    padding-top: 20px;
    border-top: 1px solid #f1f5f9;
  }

  .user-meta {
    text-align: left;
  }
}
</style>