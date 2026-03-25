<script setup>
import { onMounted, ref } from 'vue';

const themeLabel = ref(null);
const isDarkMode = ref(false);

// The original ThemeVisualizer class adapted for Vue
class ThemeVisualizer {
  constructor(canvasId, containerId, labelRef) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.container = document.getElementById(containerId);
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
    // Apply theme to the root element
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
  new ThemeVisualizer('themeCanvas', 'toggle-container', themeLabel);
});

const tabs = [
  {id: "parts", text: "Detaļu izvēlne", link: "/parts"}, 
  {id: "company", text: "Uzņēmums", link: "/company"},
  {id: "order", text: "Pasūtījumi", link: "/order"},
  {id: "warehouse", text: "Noliktva", link: "/warehouse"},
  {id: "options", text: "Iestatījumi", link: "/options"}
]

</script>

<template>
  <header>
    <ul class="tabs">
      <li v-for="tab in tabs" :key="tab.id"><router-link :to="tab.link">{{ tab.text }}</router-link></li>
      <!-- <li>Detaļu izvēlne</li>
      <li class="active">Uzņēmums</li>
      <li>Pasūtījumi</li>
      <li>Noliktava</li>
      <li>Finanses</li>
      <li>Iestatījumi</li> -->
    </ul>

    <div class="header-tools">
      <div class="user-meta">
        <strong>Jānis Bērziņš</strong>
        <span class="logout">Iziet</span>
      </div>
      
      <div id="toggle-container" title="Toggle Dark/Light Mode">
        <canvas id="themeCanvas"></canvas>
      </div>
      <div class="label-text" ref="themeLabel" v-show="false">Light Mode</div>

      <div class="btn-sq">LV</div>
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
  padding: 0 40px;
  position: relative;
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
  position: absolute;
  top: 25px;
  right: 40px;
  display: flex;
  align-items: center;
  gap: 20px;
}

#toggle-container {
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
</style>