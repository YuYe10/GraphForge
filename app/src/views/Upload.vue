<template>
  <div class="upload-page">
    <div class="page-bg"></div>

    <!-- Page Header -->
    <div class="page-header glass-card">
      <div class="header-content">
        <h1 class="page-title gradient-text-gold">知识构建</h1>
        <p class="page-subtitle">支持文件上传 · 文本输入 · 网页链接，智能构建领域知识图谱</p>
      </div>
    </div>

    <n-space vertical :size="24">
      <!-- Upload Card -->
      <n-card class="upload-card glass-card" :bordered="false">
        <n-tabs v-model:value="activeTab" type="segment" animated>
          <!-- File Upload Tab -->
          <n-tab-pane name="file" tab="📁 文件上传">
            <div class="tab-content">
              <div class="section-header">
                <n-icon size="20"><cloud-upload-outline /></n-icon>
                <h3>上传文档文件</h3>
              </div>
              <n-upload :max="1" :default-upload="false" @change="handleFileChange" :show-file-list="false" accept=".pdf,.md,.markdown,.txt,.doc,.docx">
                <n-upload-dragger class="enhanced-dragger">
                  <div class="dragger-content">
                    <div class="dragger-icon-wrapper animate-float">
                      <n-icon size="56" :component="CloudUploadOutline" class="dragger-icon" />
                    </div>
                    <div class="dragger-text">
                      <h3>点击或拖拽文件到此区域</h3>
                      <p>支持 PDF · Markdown · TXT · Word 格式</p>
                      <div class="dragger-formats">
                        <n-tag :bordered="false" size="small" type="warning">PDF</n-tag>
                        <n-tag :bordered="false" size="small" type="success">Markdown</n-tag>
                        <n-tag :bordered="false" size="small" type="info">TXT</n-tag>
                        <n-tag :bordered="false" size="small" type="error">Word</n-tag>
                      </div>
                    </div>
                  </div>
                </n-upload-dragger>
              </n-upload>

              <!-- File Selected -->
              <transition name="slide-fade">
                <div v-if="selectedFile" class="file-selected-card">
                  <div class="file-preview">
                    <div class="file-icon-wrapper">
                      <n-icon size="36" :component="DocumentTextOutline" />
                    </div>
                    <div class="file-details">
                      <div class="file-name">{{ selectedFile.name }}</div>
                      <div class="file-meta">
                        <span>{{ formatFileSize(selectedFile.size) }}</span>
                        <n-divider vertical />
                        <span class="file-type">{{ getFileType(selectedFile.name) }}</span>
                      </div>
                    </div>
                    <n-button circle quaternary @click="removeFile">
                      <template #icon><n-icon :component="CloseOutline" /></template>
                    </n-button>
                  </div>

                  <!-- Topic & AI Options -->
                  <n-form-item label="主题根节点（可选）" style="margin-top: 14px;">
                    <n-input v-model:value="rootTopic" placeholder="例如：机器学习、Web开发..." :maxlength="100" show-count clearable>
                      <template #prefix><n-icon :component="SparklesOutline" /></template>
                    </n-input>
                  </n-form-item>

                  <div class="ai-config-section">
                    <n-collapse>
                      <n-collapse-item title="🤖 AI 智能分析（可选）" name="ai-config">
                        <n-space vertical :size="12">
                          <n-switch v-model:value="enableAI">
                            <template #checked>启用 AI 深度分析</template>
                            <template #unchecked>使用传统模式</template>
                          </n-switch>
                          <n-form-item v-if="enableAI" label="自定义分析提示">
                            <n-input v-model:value="userPrompt" type="textarea" placeholder="重点关注技术架构和设计模式..." :rows="3" :maxlength="500" show-count />
                          </n-form-item>
                        </n-space>
                      </n-collapse-item>
                    </n-collapse>
                  </div>

                  <n-button type="primary" :loading="uploading" @click="handleUpload" block size="large" class="upload-btn">
                    <template #icon><n-icon><rocket-outline /></n-icon></template>
                    {{ enableAI ? '🤖 AI 智能处理' : '上传并处理' }}
                  </n-button>
                </div>
              </transition>
            </div>
          </n-tab-pane>

          <!-- Text Input Tab -->
          <n-tab-pane name="text" tab="📝 文本输入">
            <div class="tab-content">
              <div class="section-header">
                <n-icon size="20"><document-text-outline /></n-icon>
                <h3>直接输入文本内容</h3>
              </div>
              <n-form>
                <n-form-item label="文档标题（可选）">
                  <n-input v-model:value="textTitle" placeholder="为文档起个标题" :maxlength="100" show-count />
                </n-form-item>
                <n-form-item label="主题根节点（可选）">
                  <n-input v-model:value="rootTopic" placeholder="例如：机器学习、Web开发..." :maxlength="100" show-count clearable>
                    <template #prefix><n-icon :component="SparklesOutline" /></template>
                  </n-input>
                </n-form-item>
                <n-form-item label="文本内容">
                  <n-input v-model:value="textContent" type="textarea" placeholder="粘贴或输入文本内容（至少10个字符）..." :rows="12" :maxlength="100000" show-count />
                </n-form-item>
                <div class="ai-config-section">
                  <n-collapse>
                    <n-collapse-item title="🤖 AI 智能分析（可选）" name="ai-config">
                      <n-space vertical :size="12">
                        <n-switch v-model:value="enableAI" />
                        <n-form-item v-if="enableAI" label="自定义分析提示">
                          <n-input v-model:value="userPrompt" type="textarea" placeholder="..." :rows="3" :maxlength="500" show-count />
                        </n-form-item>
                      </n-space>
                    </n-collapse-item>
                  </n-collapse>
                </div>
                <n-button type="primary" :loading="uploading" :disabled="!textContent || textContent.trim().length < 10" @click="handleTextUpload" block size="large" class="upload-btn">
                  <template #icon><n-icon><rocket-outline /></n-icon></template>
                  {{ enableAI ? '🤖 AI 智能处理' : '提交文本并处理' }}
                </n-button>
              </n-form>
            </div>
          </n-tab-pane>

          <!-- URL Input Tab -->
          <n-tab-pane name="url" tab="🌐 网页链接">
            <div class="tab-content">
              <div class="section-header">
                <n-icon size="20"><globe-outline /></n-icon>
                <h3>从网页抓取内容</h3>
              </div>
              <n-form>
                <n-form-item label="网页链接">
                  <n-input v-model:value="urlInput" placeholder="输入网页 URL" :maxlength="2000">
                    <template #prefix><n-icon :component="LinkOutline" /></template>
                  </n-input>
                </n-form-item>
                <n-form-item label="文档标题（可选）">
                  <n-input v-model:value="urlTitle" placeholder="为文档起个标题" :maxlength="100" show-count />
                </n-form-item>
                <n-form-item label="主题根节点（可选）">
                  <n-input v-model:value="rootTopic" placeholder="例如：机器学习、Web开发..." :maxlength="100" show-count clearable>
                    <template #prefix><n-icon :component="SparklesOutline" /></template>
                  </n-input>
                </n-form-item>
                <div class="ai-config-section">
                  <n-collapse>
                    <n-collapse-item title="🤖 AI 智能分析（可选）" name="ai-config">
                      <n-space vertical :size="12">
                        <n-switch v-model:value="enableAI" />
                        <n-form-item v-if="enableAI" label="自定义分析提示">
                          <n-input v-model:value="userPrompt" type="textarea" placeholder="..." :rows="3" :maxlength="500" show-count />
                        </n-form-item>
                      </n-space>
                    </n-collapse-item>
                  </n-collapse>
                </div>
                <n-button type="primary" :loading="uploading" :disabled="!urlInput || !isValidUrl(urlInput)" @click="handleUrlUpload" block size="large" class="upload-btn">
                  <template #icon><n-icon><rocket-outline /></n-icon></template>
                  {{ enableAI ? '🤖 AI 智能处理' : '抓取网页并处理' }}
                </n-button>
              </n-form>
            </div>
          </n-tab-pane>
        </n-tabs>
      </n-card>

      <!-- Progress Card -->
      <transition name="slide-fade">
        <n-card v-if="currentTask" class="progress-card glass-card" :bordered="false">
          <div class="section-header">
            <n-icon size="22">
              <checkmark-circle-outline v-if="processCompleted" color="#10b981" />
              <close-outline v-else-if="processFailed" color="#ef4444" />
              <rocket-outline v-else />
            </n-icon>
            <h3>
              <span v-if="processCompleted">✨ 处理完成</span>
              <span v-else-if="processFailed">❌ 处理失败</span>
              <span v-else>⚙️ 正在处理文档</span>
            </h3>
          </div>

          <!-- Confetti on success -->
          <div v-if="processCompleted" class="confetti-container">
            <div v-for="i in 20" :key="'c'+i" class="confetti" :style="confettiStyle(i)"></div>
          </div>

          <!-- Doc Info -->
          <n-descriptions v-if="uploadResult" bordered :column="1" class="result-descriptions" style="margin-bottom: 16px">
            <n-descriptions-item label="文档 ID"><n-text code strong>{{ uploadResult.documentId }}</n-text></n-descriptions-item>
            <n-descriptions-item label="文件名"><n-text>{{ uploadResult.filename }}</n-text></n-descriptions-item>
            <n-descriptions-item v-if="currentJobId" label="任务 ID"><n-text code>{{ currentJobId }}</n-text></n-descriptions-item>
          </n-descriptions>

          <!-- Progress -->
          <div v-if="processing || processCompleted" class="progress-section">
            <div class="progress-info">
              <span class="progress-label">{{ progressMessage || '处理中...' }}</span>
              <span class="progress-percent">{{ progress }}%</span>
            </div>
            <n-progress type="line" :percentage="progress" :status="processFailed ? 'error' : processCompleted ? 'success' : 'default'" :show-indicator="false" :height="10" border-radius="5px" />
          </div>

          <!-- Stats -->
          <div v-if="processCompleted && processStats" class="stats-grid-local">
            <div class="stat-box"><div class="sv">{{ processStats.chunks }}</div><div class="sl">文本块</div></div>
            <div class="stat-box"><div class="sv">{{ processStats.triplets }}</div><div class="sl">三元组</div></div>
            <div class="stat-box"><div class="sv">{{ processStats.concepts }}</div><div class="sl">概念</div></div>
          </div>

          <!-- Error -->
          <n-alert v-if="processFailed" type="error" style="margin-top: 16px">{{ progressMessage || '处理错误' }}</n-alert>

          <!-- Actions -->
          <n-space vertical :size="12" style="margin-top: 20px">
            <n-button v-if="processCompleted" type="primary" @click="$router.push('/graph')" block size="large">查看知识图谱</n-button>
            <n-button @click="resetUpload" block size="large">
              <template #icon><n-icon><add-circle-outline /></n-icon></template>
              上传新文档
            </n-button>
          </n-space>
        </n-card>
      </transition>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { useProcessingStore } from '@/stores/processing'
import {
  CloudUploadOutline, DocumentTextOutline, CloseOutline, RocketOutline,
  CheckmarkCircleOutline, AddCircleOutline, GlobeOutline, LinkOutline, SparklesOutline
} from '@vicons/ionicons5'
import { uploadFile, uploadText, uploadUrl } from '@/api/services'

const { t } = useI18n()
void t // used in template
const message = useMessage()
const processingStore = useProcessingStore()

const activeTab = ref('file')
const selectedFile = ref<any>(null)
const textContent = ref('')
const textTitle = ref('')
const urlInput = ref('')
const urlTitle = ref('')
const rootTopic = ref('')
const enableAI = ref(false)
const userPrompt = ref('')
const uploading = ref(false)
const uploadResult = ref<any>(null)
const currentJobId = ref<string | null>(null)

const currentTask = computed(() => currentJobId.value ? processingStore.tasks.get(currentJobId.value) : null)
const processing = computed(() => currentTask.value?.status === 'processing')
const processCompleted = computed(() => currentTask.value?.status === 'completed')
const processFailed = computed(() => currentTask.value?.status === 'failed')
const progress = computed(() => currentTask.value?.progress || 0)
const progressMessage = computed(() => currentTask.value?.message || '')
const processStats = computed(() => currentTask.value?.stats)

watch(currentTask, (task) => {
  if (task?.status === 'cancelled') { uploading.value = false; resetState() }
})

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024; const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const getFileType = (filename: string) => filename.split('.').pop()?.toUpperCase() || '?'

const confettiStyle = (i: number) => ({
  '--delay': `${Math.random() * 0.5}s`,
  '--x': `${Math.random() * 100}%`,
  '--rotation': `${Math.random() * 720}deg`,
  background: ['#d4af37', '#c9a668', '#9b87f5', '#10b981', '#f59e0b', '#3b82f6'][i % 6],
  left: `${10 + (i % 8) * 10}%`,
  animationDelay: `${i * 0.08}s`,
  animationDuration: `${1.5 + Math.random() * 2}s`
})

const ALLOWED_EXTENSIONS = ['.pdf', '.md', '.markdown', '.txt', '.doc', '.docx']
const ALLOWED_MIME_TYPES = ['application/pdf', 'text/markdown', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']

const validateFileType = (file: { name: string; type?: string }) => {
  const ext = '.' + file.name.toLowerCase().split('.').pop()
  if (!ALLOWED_EXTENSIONS.includes(ext)) return false
  if (file.type && !ALLOWED_MIME_TYPES.includes(file.type) && !['.md', '.markdown'].includes(ext)) return false
  return true
}

const handleFileChange = ({ file }: any) => {
  if (file && validateFileType(file.file)) {
    selectedFile.value = file.file
    resetState()
    message.success(`已选择文件: ${file.file.name}`)
  } else {
    message.error('不支持的文件类型')
  }
}

const removeFile = () => { selectedFile.value = null; resetState() }
const resetState = () => { uploadResult.value = null; currentJobId.value = null }

const isValidUrl = (url: string) => { try { const u = new URL(url); return u.protocol === 'http:' || u.protocol === 'https:' } catch { return false } }

const buildOptions = () => {
  const base: any = { rootTopic: rootTopic.value || undefined }
  if (enableAI.value) {
    base.enableAI = true
    if (userPrompt.value) base.userPrompt = userPrompt.value
  }
  return base
}

const handleUpload = async () => {
  if (!selectedFile.value) { message.warning('请选择文件'); return }
  uploading.value = true; resetState()
  try {
    const result = await uploadFile(selectedFile.value, buildOptions())
    uploadResult.value = result
    if (result.status === 'duplicate') { message.warning(result.message || '文档已存在'); uploading.value = false; return }
    if (result.jobId) {
      message.success('文件上传成功，开始处理...')
      uploading.value = false
      currentJobId.value = result.jobId
      processingStore.addTask({ jobId: result.jobId, documentId: result.documentId, filename: result.filename, status: 'processing', progress: 0, message: '开始处理...' })
    }
  } catch (error: any) { message.error('上传失败: ' + error.message); uploading.value = false }
}

const handleTextUpload = async () => {
  if (!textContent.value || textContent.value.trim().length < 10) { message.error('文本内容至少10个字符'); return }
  uploading.value = true; resetState()
  try {
    const result = await uploadText(textContent.value, textTitle.value || undefined, true, buildOptions())
    uploadResult.value = result
    if (result.status === 'duplicate') { message.warning('文档已存在'); uploading.value = false; return }
    if (result.jobId) {
      message.success('文本已提交，开始处理...')
      uploading.value = false; currentJobId.value = result.jobId
      processingStore.addTask({ jobId: result.jobId, documentId: result.documentId, filename: result.filename, status: 'processing', progress: 0, message: '开始处理...' })
    }
    textContent.value = ''; textTitle.value = ''; rootTopic.value = ''
  } catch (error: any) { message.error('提交失败: ' + error.message); uploading.value = false }
}

const handleUrlUpload = async () => {
  if (!urlInput.value || !isValidUrl(urlInput.value)) { message.error('请输入有效URL'); return }
  uploading.value = true; resetState()
  try {
    const result = await uploadUrl(urlInput.value, urlTitle.value || undefined, true, buildOptions())
    uploadResult.value = result
    if (result.status === 'duplicate') { message.warning('内容已存在'); uploading.value = false; return }
    if (result.jobId) {
      message.success('网页已抓取，开始处理...')
      uploading.value = false; currentJobId.value = result.jobId
      processingStore.addTask({ jobId: result.jobId, documentId: result.documentId, filename: result.filename, status: 'processing', progress: 0, message: '开始处理...' })
    }
    urlInput.value = ''; urlTitle.value = ''; rootTopic.value = ''
  } catch (error: any) { message.error('抓取失败: ' + error.message); uploading.value = false }
}

const resetUpload = () => {
  selectedFile.value = null; textContent.value = ''; textTitle.value = ''
  urlInput.value = ''; urlTitle.value = ''; rootTopic.value = ''
  resetState(); activeTab.value = 'file'
}
</script>

<style lang="scss" scoped>
.upload-page {
  padding: 28px 40px;
  min-height: calc(100vh - 64px);
  position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background:
      radial-gradient(ellipse at 20% 20%, rgba(194, 164, 116, 0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, rgba(155, 135, 245, 0.06) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.page-header {
  margin-bottom: 28px;
  padding: 28px 32px;

  .page-title { font-size: 32px; font-weight: 800; margin: 0 0 6px; letter-spacing: -0.5px; }
  .page-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
}

.section-header {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 20px; padding-bottom: 14px;
  border-bottom: 2px solid rgba(194, 164, 116, 0.1);

  .n-icon { color: var(--color-primary-light); }
  h3 { font-size: 17px; font-weight: 700; margin: 0; color: var(--color-text); }
}

.upload-card {
  .tab-content { padding: 16px 0; }
}

// Enhanced Dragger
.enhanced-dragger {
  :deep(.n-upload-dragger) {
    padding: 56px 40px;
    border: 2px dashed rgba(194, 164, 116, 0.25);
    border-radius: var(--radius-xl);
    background: linear-gradient(135deg, rgba(255,255,255,0.5), rgba(248,250,252,0.5));
    transition: all var(--transition-base);
    position: relative; overflow: hidden;

    &::before {
      content: ''; position: absolute; inset: 0;
      background: radial-gradient(circle at 30% 40%, rgba(194,164,116,0.04) 0%, transparent 60%),
                  radial-gradient(circle at 70% 60%, rgba(155,135,245,0.04) 0%, transparent 60%);
      pointer-events: none;
    }

    &:hover {
      border-color: rgba(194, 164, 116, 0.5);
      background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(248,250,252,0.8));
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(194,164,116,0.12);
    }
  }

  .dragger-content {
    display: flex; flex-direction: column; align-items: center; gap: 16px;
    position: relative; z-index: 1;
  }

  .dragger-icon { color: var(--color-primary-light); }
  .dragger-text {
    text-align: center;
    h3 { font-size: 19px; font-weight: 700; color: var(--color-text); margin: 0 0 6px; }
    p { font-size: 13px; color: var(--color-text-muted); margin: 0 0 12px; }
    .dragger-formats { display: flex; gap: 8px; justify-content: center; }
  }
}

// File Selected Card
.file-selected-card {
  margin-top: 24px; padding: 24px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, rgba(194,164,116,0.06), rgba(155,135,245,0.06));
  border: 1px solid rgba(194,164,116,0.15);
  box-shadow: var(--shadow-sm);

  .file-preview {
    display: flex; align-items: center; gap: 14px;
    padding: 18px; border-radius: var(--radius-lg);
    background: rgba(255,255,255,0.95); border: 1px solid rgba(194,164,116,0.12);
    transition: all var(--transition-fast);

    &:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
    .file-icon-wrapper {
      width: 50px; height: 50px; border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--color-primary-light), var(--color-accent));
      display: flex; align-items: center; justify-content: center;
      color: white; flex-shrink: 0; box-shadow: 0 4px 12px rgba(194,164,116,0.3);
    }
    .file-details {
      flex: 1;
      .file-name { font-size: 15px; font-weight: 700; color: var(--color-text); margin-bottom: 4px; }
      .file-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--color-text-muted); }
      .file-type { font-weight: 700; color: var(--color-primary-light); }
    }
  }

  .upload-btn {
    margin-top: 12px; height: 48px; font-size: 16px; font-weight: 700;
    border-radius: var(--radius-md) !important;
  }
}

.ai-config-section {
  margin: 14px 0;
  :deep(.n-collapse) {
    border-radius: var(--radius-lg); overflow: hidden;
    background: linear-gradient(135deg, rgba(194,164,116,0.04), rgba(155,135,245,0.04));
    border: 1px solid rgba(194,164,116,0.12);
  }
}

// Progress Card
.progress-card {
  .progress-section {
    padding: 18px; border-radius: var(--radius-lg);
    background: linear-gradient(135deg, rgba(194,164,116,0.04), rgba(155,135,245,0.04));
    margin-bottom: 14px;

    .progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .progress-label { font-size: 13px; font-weight: 600; color: var(--color-text); }
    .progress-percent { font-size: 18px; font-weight: 800; color: var(--color-primary-light); }
  }

  .stats-grid-local {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 16px;
    .stat-box {
      padding: 14px; border-radius: var(--radius-lg); text-align: center;
      background: rgba(255,255,255,0.8); border: 1px solid rgba(194,164,116,0.12);
      transition: all var(--transition-fast);
      &:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
      .sv { font-size: 26px; font-weight: 800; color: var(--color-primary-dark); }
      .sl { font-size: 12px; color: var(--color-text-muted); font-weight: 500; }
    }
  }
}

// Confetti
.confetti-container {
  position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 5;
  .confetti {
    position: absolute; top: -10px;
    width: 8px; height: 8px; border-radius: 2px;
    animation: confetti-fall var(--duration, 2.5s) ease-in var(--delay, 0s) forwards;
  }
}

@keyframes confetti-fall {
  0% { transform: translateY(-10px) rotate(0deg); opacity: 1; }
  100% { transform: translateY(400px) rotate(var(--rotation, 720deg)); opacity: 0; }
}

// Transitions
.slide-fade-enter-active { transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(0.4, 0, 1, 1); }
.slide-fade-enter-from { opacity: 0; transform: translateY(20px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-20px); }
</style>
