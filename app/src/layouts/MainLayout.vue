<template>
  <n-layout class="main-layout">
    <!-- Animated Background -->
    <div class="layout-bg"></div>

    <!-- Top Header with Glassmorphism -->
    <n-layout-header bordered class="header glass-strong">
      <div class="header-inner">
        <!-- Logo -->
        <div class="header-logo" @click="$router.push('/')">
          <div class="logo-icon animate-float">
            <n-icon size="28"><cube-outline /></n-icon>
          </div>
          <div class="logo-text">
            <h2 class="logo-title gradient-text-gold">{{ t('app.title') }}</h2>
          </div>
        </div>

        <!-- Search Bar -->
        <div class="header-search">
          <n-input
            round
            clearable
            placeholder="搜索节点、文档、概念..."
            :style="{ width: '320px' }"
          >
            <template #prefix>
              <n-icon><search-outline /></n-icon>
            </template>
          </n-input>
        </div>

        <!-- Navigation Menu -->
        <div class="header-nav">
          <div
            v-for="item in menuOptions"
            :key="item.key"
            :class="['nav-item', { active: activeKey === item.key || activeKey.startsWith(item.key + '/') }]"
            @click="handleMenuSelect(item.key)"
          >
            <n-icon v-if="item.icon" size="16">
              <component :is="item.icon" />
            </n-icon>
            <span>{{ item.label }}</span>
            <div v-if="activeKey === item.key || activeKey.startsWith(item.key + '/')" class="nav-indicator"></div>
          </div>
        </div>

        <!-- Right Actions -->
        <div class="header-right">
          <n-space :size="8" align="center">
            <!-- Theme Toggle -->
            <n-button text circle @click="toggleTheme" class="header-btn">
              <template #icon>
                <n-icon size="18">
                  <sunny-outline v-if="themeMode === 'dark'" />
                  <moon-outline v-else />
                </n-icon>
              </template>
            </n-button>

            <!-- Language Selector -->
            <n-dropdown trigger="hover" :options="languageOptions" @select="handleLanguageChange">
              <n-button text class="header-btn">
                <template #icon>
                  <n-icon size="18"><globe-outline /></n-icon>
                </template>
                <span class="lang-label">{{ currentLangLabel }}</span>
              </n-button>
            </n-dropdown>

            <!-- Notifications -->
            <n-badge :value="processingStore.processingCount" :max="99" :show-zero="false" processing>
              <n-button text circle class="header-btn" @click="processingStore.showFloater()">
                <template #icon>
                  <n-icon size="20"><notifications-outline /></n-icon>
                </template>
              </n-button>
            </n-badge>

            <!-- User Menu -->
            <n-dropdown trigger="hover" :options="userMenuOptions" @select="handleUserMenuSelect">
              <n-button text class="header-btn user-btn">
                <n-avatar round :size="34" src="https://07akioni.oss-cn-beijing.aliyuncs.com/07akioni.jpeg" />
              </n-button>
            </n-dropdown>
          </n-space>
        </div>
      </div>
    </n-layout-header>

    <!-- Breadcrumb -->
    <div v-if="breadcrumbs.length > 1" class="breadcrumb-bar">
      <n-breadcrumb>
        <n-breadcrumb-item
          v-for="(crumb, idx) in breadcrumbs"
          :key="idx"
          @click="idx < breadcrumbs.length - 1 && $router.push(crumb.path)"
        >
          {{ crumb.label }}
        </n-breadcrumb-item>
      </n-breadcrumb>
    </div>

    <!-- Main Content Area -->
    <n-layout>
      <n-layout-content :native-scrollbar="false" class="main-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component, route: r }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" :key="r.path" />
            </transition>
          </router-view>
        </div>
      </n-layout-content>
    </n-layout>

    <!-- Global Processing Floater -->
    <processing-floater />

    <!-- Command Palette (Ctrl+K) -->
    <CommandPalette v-model:visible="showCommandPalette" />
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import { useProcessingStore } from '@/stores/processing'
import ProcessingFloater from '@/components/ProcessingFloater.vue'
import CommandPalette from '@/components/CommandPalette.vue'
import {
  CubeOutline, GlobeOutline, NotificationsOutline,
  SearchOutline, SunnyOutline, MoonOutline,
  GridOutline, CloudUploadOutline, DocumentTextOutline,
  GitNetworkOutline, CodeSlashOutline, TimeOutline,
  OptionsOutline
} from '@vicons/ionicons5'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const appStore = useAppStore()
const processingStore = useProcessingStore()

const activeKey = ref(route.path)
const themeMode = ref(localStorage.getItem('graphforge-theme') || 'light')
const showCommandPalette = ref(false)

// Global keyboard shortcuts
const handleGlobalKeydown = (e: KeyboardEvent) => {
  // Ctrl+K / Cmd+K → Command Palette
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    showCommandPalette.value = !showCommandPalette.value
  }
  // Escape → Close palette
  if (e.key === 'Escape' && showCommandPalette.value) {
    showCommandPalette.value = false
  }
}

const toggleTheme = () => {
  themeMode.value = themeMode.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('graphforge-theme', themeMode.value)
  if ((window as any).__graphforgeTheme) {
    (window as any).__graphforgeTheme.mode.value = themeMode.value
  }
  document.documentElement.classList.toggle('dark', themeMode.value === 'dark')
}

// Menu Options with icons
const menuOptions = computed(() => [
  { label: t('navigation.dashboard'), key: '/', icon: GridOutline },
  { label: t('navigation.knowledge_build'), key: '/knowledge', icon: CloudUploadOutline },
  { label: '文档管理', key: '/documents', icon: DocumentTextOutline },
  { label: t('navigation.knowledge_card'), key: '/knowledge-card', icon: OptionsOutline },
  { label: t('navigation.graph_visualization'), key: '/graph', icon: GitNetworkOutline },
  { label: t('navigation.query'), key: '/query', icon: CodeSlashOutline },
  { label: t('navigation.status'), key: '/status', icon: TimeOutline }
])

// Breadcrumbs
const breadcrumbs = computed(() => {
  const crumbs: { label: string; path: string }[] = [{ label: '首页', path: '/' }]
  const menuItem = menuOptions.value.find(m => m.key !== '/' && route.path.startsWith(m.key))
  if (menuItem) crumbs.push({ label: menuItem.label, path: menuItem.key })
  return crumbs
})

// Language
const currentLangLabel = computed(() => locale.value === 'zh' ? '中文' : 'English')
const languageOptions = [
  { label: '中文', key: 'zh' },
  { label: 'English', key: 'en' }
]

// User Menu
const userMenuOptions = computed(() => [
  { label: t('common.profile'), key: 'profile' },
  { label: t('common.settings'), key: 'settings' },
  { type: 'divider' as const },
  { label: t('common.logout'), key: 'logout' }
])

// Handlers
const handleMenuSelect = (key: string) => {
  activeKey.value = key
  router.push(key)
}

const handleLanguageChange = (key: string) => {
  appStore.setLanguage(key as 'zh' | 'en')
  locale.value = key as 'zh' | 'en'
}

const handleUserMenuSelect = (key: string) => {
  if (key === 'settings') router.push('/settings')
  else if (key === 'logout') {
    if (window.$dialog) {
      window.$dialog.info({ title: '提示', content: '退出登录功能开发中' })
    }
  }
}

watch(() => route.path, (newPath) => {
  activeKey.value = newPath
}, { immediate: true })

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style lang="scss" scoped>
.main-layout {
  min-height: 100vh;
  background: var(--color-bg);
  position: relative;
}

.layout-bg {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 0%, rgba(194, 164, 116, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(155, 135, 245, 0.06) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(245, 158, 11, 0.03) 0%, transparent 60%);
  pointer-events: none;
  z-index: 0;
}

// ============================================================
// Header — Glassmorphism
// ============================================================
.header {
  height: 64px;
  position: sticky !important;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(194, 164, 116, 0.15) !important;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.04);
  transition: all var(--transition-base);

  &.header--scrolled {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }
}

.header-inner {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 0 32px;
  gap: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  flex-shrink: 0;
  user-select: none;

  .logo-icon {
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #d4af37, #b8860b);
    border-radius: 10px;
    color: #fff;
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.35);
  }

  .logo-text {
    .logo-title {
      margin: 0;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.3px;
    }
  }
}

// Search
.header-search {
  flex-shrink: 0;

  :deep(.n-input) {
    --n-border-radius: 20px;
    --n-border: 1px solid rgba(194, 164, 116, 0.15);
    --n-border-hover: 1px solid rgba(194, 164, 116, 0.35);
    --n-border-focus: 1px solid rgba(194, 164, 116, 0.5);
    --n-box-shadow-focus: 0 0 0 3px rgba(194, 164, 116, 0.12);
    transition: all var(--transition-base);

    &:hover { --n-box-shadow: 0 2px 8px rgba(194, 164, 116, 0.12); }
  }
}

// Navigation
.header-nav {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
  justify-content: center;

  .nav-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    color: var(--color-text-secondary);
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    white-space: nowrap;
    position: relative;

    &:hover {
      color: var(--color-text);
      background: var(--color-primary-subtle);
    }

    &.active {
      color: var(--color-primary-dark);
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.12), rgba(218, 165, 32, 0.08));
      font-weight: 600;
    }

    .nav-indicator {
      position: absolute;
      bottom: -1px;
      left: 50%;
      transform: translateX(-50%);
      width: 20px;
      height: 2px;
      background: linear-gradient(90deg, var(--color-primary-light), var(--color-accent));
      border-radius: 1px;
    }
  }
}

// Right actions
.header-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;

  .lang-label {
    font-size: 13px;
    font-weight: 500;
    margin-left: 4px;
  }

  :deep(.header-btn) {
    color: var(--color-text-secondary);
    transition: all var(--transition-fast);

    &:hover {
      color: var(--color-text);
      background: var(--color-primary-subtle);
    }
  }

  :deep(.user-btn:hover .n-avatar) {
    border-color: var(--color-primary-light);
    transform: scale(1.08);
    box-shadow: 0 4px 12px rgba(212, 175, 55, 0.35);
  }

  :deep(.n-avatar) {
    border: 2px solid var(--color-border);
    transition: all var(--transition-base);
    cursor: pointer;
  }
}

// ============================================================
// Breadcrumb Bar
// ============================================================
.breadcrumb-bar {
  padding: 12px 32px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-border-light);

  :deep(.n-breadcrumb) {
    font-size: 13px;
    font-weight: 500;

    .n-breadcrumb-item__link {
      color: var(--color-text-secondary);
      transition: color var(--transition-fast);
      &:hover { color: var(--color-primary-dark); }
    }
    .n-breadcrumb-item--last .n-breadcrumb-item__link { color: var(--color-text); }
  }
}

// ============================================================
// Main Content
// ============================================================
.main-content {
  padding: 0;
  min-height: calc(100vh - 64px);
  background: transparent;

  .content-wrapper {
    width: 100%;
    height: 100%;
  }
}

// Page transitions
.fade-slide-enter-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.fade-slide-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 1, 1); }
.fade-slide-enter-from { opacity: 0; transform: translateY(20px) scale(0.97); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-10px); }

// Responsive
@media (max-width: 1200px) {
  .header-search { display: none; }
  .header-nav .nav-item { padding: 8px 10px; font-size: 12px; gap: 4px; }
}

@media (max-width: 768px) {
  .header-inner { padding: 0 16px; gap: 8px; }
  .header-nav { gap: 0; }
  .header-nav .nav-item span { display: none; }
}
</style>
