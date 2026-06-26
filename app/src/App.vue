<template>
  <n-config-provider :locale="naiveLocale" :date-locale="naiveDateLocale" :theme="naiveTheme">
    <n-global-style />
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <AppContent />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NConfigProvider, NMessageProvider, NNotificationProvider,
  NDialogProvider, NGlobalStyle,
  zhCN, enUS, dateZhCN, dateEnUS,
  darkTheme
} from 'naive-ui'
import AppContent from './components/AppContent.vue'

const { locale } = useI18n()

// Theme system — null = light, darkTheme = dark
const themeMode = ref(localStorage.getItem('graphforge-theme') || 'light')
const naiveTheme = computed(() => themeMode.value === 'dark' ? darkTheme : null)

// Expose theme toggle globally
if (typeof window !== 'undefined') {
  ;(window as any).__graphforgeTheme = {
    mode: themeMode,
    toggle: () => {
      themeMode.value = themeMode.value === 'dark' ? 'light' : 'dark'
      localStorage.setItem('graphforge-theme', themeMode.value)
    }
  }
}

// Apply theme class to html element
watch(themeMode, (mode) => {
  document.documentElement.classList.toggle('dark', mode === 'dark')
}, { immediate: true })

const naiveLocale = computed(() => locale.value === 'zh' ? zhCN : enUS)
const naiveDateLocale = computed(() => locale.value === 'zh' ? dateZhCN : dateEnUS)

// Background particles
let particlesCanvas: HTMLCanvasElement | null = null
let particlesAnimationId = 0

onMounted(() => {
  initParticles()
})

onUnmounted(() => {
  if (particlesAnimationId) cancelAnimationFrame(particlesAnimationId)
  particlesCanvas?.remove()
})

function initParticles() {
  particlesCanvas = document.createElement('canvas')
  particlesCanvas.id = 'particles-canvas'
  particlesCanvas.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:0;opacity:0.25;'
  document.body.appendChild(particlesCanvas)

  const ctx = particlesCanvas.getContext('2d')
  if (!ctx) return

  const resize = () => {
    if (!particlesCanvas) return
    particlesCanvas.width = window.innerWidth
    particlesCanvas.height = window.innerHeight
  }
  resize()
  window.addEventListener('resize', resize)

  interface Particle {
    x: number; y: number; vx: number; vy: number; size: number; opacity: number; life: number; maxLife: number
  }

  const particles: Particle[] = []
  const MAX_PARTICLES = 30

  function createParticle(): Particle {
    return {
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.5 + 0.1,
      life: 0,
      maxLife: Math.random() * 300 + 200
    }
  }

  for (let i = 0; i < MAX_PARTICLES; i++) {
    particles.push(createParticle())
  }

  function animate() {
    if (!ctx || !particlesCanvas) return
    ctx.clearRect(0, 0, particlesCanvas.width, particlesCanvas.height)

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i]
      p.x += p.vx
      p.y += p.vy
      p.life++

      // Wrap around edges
      if (p.x < -10) p.x = window.innerWidth + 10
      if (p.x > window.innerWidth + 10) p.x = -10
      if (p.y < -10) p.y = window.innerHeight + 10
      if (p.y > window.innerHeight + 10) p.y = -10

      const fadeRatio = Math.sin((p.life / p.maxLife) * Math.PI)
      const alpha = p.opacity * fadeRatio

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(194, 164, 116, ${alpha})`
      ctx.fill()

      // Draw connections between nearby particles
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j]
        const dx = p.x - p2.x
        const dy = p.y - p2.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < 150) {
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(p2.x, p2.y)
          ctx.strokeStyle = `rgba(194, 164, 116, ${0.06 * (1 - dist / 150)})`
          ctx.lineWidth = 0.5
          ctx.stroke()
        }
      }

      // Respawn dead particles
      if (p.life >= p.maxLife) {
        particles[i] = createParticle()
      }
    }

    particlesAnimationId = requestAnimationFrame(animate)
  }

  animate()
}
</script>

<style lang="scss">
// ============================================================
// GraphForge App — Global Component Styles
// International Design Excellence
// ============================================================

// --- Theme Variables (Dark Mode) ---
html.dark {
  #app {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    color: #e2e8f0;
  }

  // cards adapt
  :deep(.n-card) {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: rgba(71, 85, 105, 0.3) !important;
  }

  :deep(.n-layout) { background: transparent !important; }
  :deep(.n-layout-header) { background: rgba(15, 23, 42, 0.9) !important; }
}

// --- Base ---
* { margin: 0; padding: 0; box-sizing: border-box; }

#app {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
}

// --- Global Card Styles ---
:deep(.n-card) {
  border-radius: var(--radius-xl) !important;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);

  &.n-card--hoverable:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg), 0 0 30px var(--color-primary-glow);
  }

  > .n-card-header {
    font-weight: 700;
    font-size: 17px;
    padding: 20px 24px 16px;
    border-bottom: 1px solid var(--color-border-light);
    letter-spacing: -0.2px;
  }

  > .n-card__content {
    padding: 24px;
  }

  > .n-card__footer {
    padding: 16px 24px;
    border-top: 1px solid var(--color-border-light);
  }
}

// --- Global Button Styles — Luxurious Gold Theme ---
:deep(.n-button) {
  border-radius: var(--radius-md) !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px;
  transition: all var(--transition-base) !important;

  &:focus { outline: none !important; }

  // Primary — Gold gradient
  &.n-button--primary-type {
    background: linear-gradient(135deg, #d4af37, #b8860b) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #c9a668, #9a7509) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(212, 175, 55, 0.45);
    }

    &:active:not(:disabled) {
      background: linear-gradient(135deg, #b8860b, #8b6914) !important;
      transform: translateY(0);
    }

    &:focus:not(:disabled) {
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3);
    }
  }

  // Default
  &.n-button--default-type {
    background: var(--color-surface);
    border: 1px solid #e0e0e0 !important;
    color: var(--color-text-secondary);

    &:hover:not(:disabled) {
      background: var(--color-surface-alt);
      border-color: var(--color-primary-light) !important;
      color: var(--color-primary-dark);
      transform: translateY(-2px);
    }

    &:focus:not(:disabled) {
      border-color: var(--color-primary-light) !important;
      box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.15);
    }
  }

  // Success
  &.n-button--success-type {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    border: none !important;
    color: #fff !important;
    box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #34d399, #10b981) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45);
    }
  }

  // Warning
  &.n-button--warning-type {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    border: none !important;
    color: #fff !important;

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #fbbf24, #f59e0b) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(245, 158, 11, 0.45);
    }
  }

  // Error
  &.n-button--error-type {
    background: linear-gradient(135deg, #ef4444, #dc2626) !important;
    border: none !important;
    color: #fff !important;

    &:hover:not(:disabled) {
      background: linear-gradient(135deg, #f87171, #ef4444) !important;
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45);
    }
  }

  // Text buttons
  &.n-button--text-type {
    border: none !important;
    background: transparent;

    &.n-button--primary-type {
      color: var(--color-primary-light);
      &:hover:not(:disabled) { background: var(--color-primary-subtle) !important; color: var(--color-primary-dark); }
    }
    &.n-button--error-type {
      color: var(--color-error);
      &:hover:not(:disabled) { background: rgba(239, 68, 68, 0.1) !important; }
    }
  }

  // Ghost
  &.n-button--ghost-type {
    border-color: var(--color-primary-light) !important;
    color: var(--color-primary-light);
    &:hover:not(:disabled) {
      background: var(--color-primary-subtle) !important;
      border-color: var(--color-primary-dark) !important;
    }
  }
}

// --- Global Input Styles ---
:deep(.n-input),
:deep(.n-input-number),
:deep(.n-select) {
  .n-input__border,
  .n-input__state-border,
  .n-base-selection {
    border-radius: var(--radius-md) !important;
  }
}

:deep(.n-input) {
  textarea {
    font-family: var(--font-mono);
    font-size: 14px;
    line-height: 1.7;
  }
}

// --- Global Tag Styles ---
:deep(.n-tag) {
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.2px;
  transition: all var(--transition-fast);

  &.n-tag--round { border-radius: 16px; }

  &:hover { transform: scale(1.05); }
}

// --- Global Alert Styles ---
:deep(.n-alert) {
  border-radius: var(--radius-lg);
  border-left-width: 4px;
  font-weight: 500;
}

// --- Global Table Styles ---
:deep(.n-data-table) {
  border-radius: var(--radius-xl);
  overflow: hidden;

  .n-data-table-th {
    background: linear-gradient(135deg, rgba(194, 164, 116, 0.06), rgba(155, 135, 245, 0.04));
    font-weight: 700;
    font-size: 13px;
    color: var(--color-text);
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }

  .n-data-table-td {
    padding: 14px 16px;
    font-size: 14px;
  }

  .n-data-table-tr {
    transition: background var(--transition-fast);

    &:hover .n-data-table-td {
      background: rgba(194, 164, 116, 0.04);
    }
  }
}

// --- Global Progress ---
:deep(.n-progress) {
  .n-progress-graph-line-fill {
    background: linear-gradient(90deg, var(--color-primary-light), var(--color-accent), var(--color-primary-dark));
    background-size: 200% 100%;
    animation: gradientFlow 3s ease infinite;
  }
}

// --- Global Modal/Drawer ---
:deep(.n-modal) {
  .n-dialog {
    border-radius: var(--radius-2xl) !important;
    overflow: hidden;
  }
  .n-dialog__title {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.3px;
  }
}

:deep(.n-drawer) {
  .n-drawer-header {
    font-weight: 700;
    font-size: 18px;
    letter-spacing: -0.2px;
    border-bottom: 1px solid var(--color-border-light);
  }
}

// --- Global Spin ---
:deep(.n-spin) {
  .n-spin-description {
    margin-top: 12px;
    font-weight: 600;
    color: var(--color-text-secondary);
  }
}

// --- Global Tabs ---
:deep(.n-tabs) {
  .n-tabs-nav {
    border-radius: var(--radius-lg);
    padding: 4px;
  }

  .n-tabs-tab {
    font-weight: 600;
    border-radius: var(--radius-md);
    transition: all var(--transition-base);

    &.n-tabs-tab--active {
      background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
      box-shadow: var(--shadow-sm);
    }
  }
}

// --- Global Collapse ---
:deep(.n-collapse) {
  border-radius: var(--radius-lg);
  overflow: hidden;

  .n-collapse-item__header {
    font-weight: 600;
    transition: all var(--transition-fast);
  }
}

// --- Global Divider ---
:deep(.n-divider) {
  .n-divider__line {
    background: var(--color-border-light);
  }
}

// --- Notification animation ---
:deep(.n-notification) {
  border-radius: var(--radius-lg) !important;
  box-shadow: var(--shadow-lg) !important;
  animation: slideInUp 0.4s ease-out !important;
}

// --- Transition animations ---
.fade-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-slide-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 1, 1);
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.98);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

// --- Link styles ---
a {
  color: var(--color-primary-dark);
  text-decoration: none;
  transition: color var(--transition-fast);
  &:hover { color: var(--color-primary-light); }
}
</style>
