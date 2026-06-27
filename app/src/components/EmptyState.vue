<template>
  <div class="empty-state-wrapper">
    <div class="empty-illustration" :class="`illustration-${type}`">
      <!-- Animated geometric shapes instead of images -->
      <div class="geo-circle geo-1"></div>
      <div class="geo-circle geo-2"></div>
      <div class="geo-circle geo-3"></div>
      <div class="geo-diamond geo-4"></div>
      <div class="geo-square geo-5"></div>

      <!-- Central icon -->
      <div class="empty-icon">
        <n-icon :size="iconSize" :color="iconColor">
          <component :is="icon" />
        </n-icon>
      </div>
    </div>

    <h3 class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-description">{{ description }}</p>

    <div v-if="$slots.default || actionLabel" class="empty-actions">
      <slot>
        <n-button v-if="actionLabel" type="primary" @click="$emit('action')" size="large" secondary>
          <template v-if="actionIcon" #icon>
            <n-icon><component :is="actionIcon" /></n-icon>
          </template>
          {{ actionLabel }}
        </n-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NIcon, NButton } from 'naive-ui'
import {
  DocumentTextOutline, CubeOutline, SearchOutline,
  CloudUploadOutline, GitNetworkOutline, ChatbubbleOutline,
  ServerOutline, FolderOpenOutline
} from '@vicons/ionicons5'

const props = withDefaults(defineProps<{
  type?: 'document' | 'data' | 'search' | 'upload' | 'graph' | 'chat' | 'server' | 'folder'
  title?: string
  description?: string
  actionLabel?: string
  actionIcon?: any
  iconSize?: number
}>(), {
  type: 'data',
  title: '暂无数据',
  description: '',
  actionLabel: '',
  iconSize: 48
})

defineEmits<{ action: [] }>()

const iconMap: Record<string, any> = {
  document: DocumentTextOutline,
  data: CubeOutline,
  search: SearchOutline,
  upload: CloudUploadOutline,
  graph: GitNetworkOutline,
  chat: ChatbubbleOutline,
  server: ServerOutline,
  folder: FolderOpenOutline
}

const icon = computed(() => iconMap[props.type] || iconMap.data)

const colorMap: Record<string, string> = {
  document: '#d4af37',
  data: '#9b87f5',
  search: '#3b82f6',
  upload: '#10b981',
  graph: '#f59e0b',
  chat: '#8b5cf6',
  server: '#6366f1',
  folder: '#c2a474'
}

const iconColor = computed(() => colorMap[props.type] || '#9b87f5')
</script>

<style lang="scss" scoped>
.empty-state-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  animation: fadeInUp 0.6s ease-out both;
}

// Animated geometric illustration
.empty-illustration {
  position: relative;
  width: 140px;
  height: 140px;
  margin-bottom: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

// Geometric shapes
[class*="geo-"] {
  position: absolute;
  opacity: 0.12;
  transition: all 0.6s ease;
}

.geo-circle {
  border-radius: 50%;
}

.geo-1 {
  width: 100px; height: 100px;
  background: var(--color-primary-light, #c2a474);
  animation: geoFloat1 4s ease-in-out infinite;
  top: 10px; left: 20px;
}

.geo-2 {
  width: 60px; height: 60px;
  background: var(--color-accent, #9b87f5);
  animation: geoFloat2 5s ease-in-out infinite;
  top: 50px; right: 10px;
}

.geo-3 {
  width: 40px; height: 40px;
  background: #f59e0b;
  animation: geoFloat3 3.5s ease-in-out infinite;
  bottom: 5px; left: 15px;
}

.geo-diamond {
  width: 30px; height: 30px;
  background: #10b981;
  transform: rotate(45deg);
  animation: geoFloat1 4.5s ease-in-out infinite reverse;
  top: 0; right: 30px;
  border-radius: 4px;
}

.geo-square {
  width: 24px; height: 24px;
  background: #3b82f6;
  animation: geoFloat2 3.8s ease-in-out infinite reverse;
  bottom: 20px; right: 20px;
  border-radius: 4px;
}

// Central icon
.empty-icon {
  position: relative;
  z-index: 2;
  width: 72px; height: 72px;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.8);
}

.empty-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 8px;
  letter-spacing: -0.2px;
}

.empty-description {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0 0 24px;
  max-width: 360px;
  line-height: 1.5;
}

.empty-actions {
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

@keyframes geoFloat1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6px, -8px) scale(1.05); }
  66% { transform: translate(-4px, 4px) scale(0.95); }
}

@keyframes geoFloat2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-8px, 6px) scale(1.08); }
}

@keyframes geoFloat3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(8px, -4px) scale(1.1); }
}
</style>
