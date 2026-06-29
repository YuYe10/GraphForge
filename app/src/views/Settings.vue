<template>
  <div class="settings-view">
    <div class="page-bg"></div>

    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header glass-card">
        <h1 class="title gradient-text-purple">{{ t('settings.title') }}</h1>
        <p class="subtitle">{{ t('settings.subtitle') }}</p>
      </div>

      <!-- AI Provider Settings -->
      <n-card :title="t('settings.ai_provider')" class="settings-card glass-card">
        <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="140" require-mark-placement="right-hanging">
          <n-form-item :label="t('settings.provider_type')" path="ai_provider">
            <n-select v-model:value="formData.ai_provider" :options="providerOptions" :loading="loadingProviders" @update:value="handleProviderChange" />
          </n-form-item>

          <template v-if="formData.ai_provider !== 'mock'">
            <n-form-item v-if="currentProvider?.requires_api_key" :label="t('settings.api_key')" path="ai_api_key">
              <n-input v-model:value="formData.ai_api_key" type="password" show-password-on="click" :placeholder="t('settings.api_key_placeholder')" />
            </n-form-item>

            <n-form-item :label="t('settings.model')" path="ai_model">
              <n-space vertical style="width: 100%">
                <n-select v-if="formData.ai_provider === 'ollama'" v-model:value="formData.ai_model" :options="ollamaModelOptions" :loading="loadingModels" filterable tag :placeholder="currentProvider?.default_model || '选择模型'" />
                <n-input v-else v-model:value="formData.ai_model" :placeholder="currentProvider?.default_model || t('settings.model_placeholder')" />
                <n-button v-if="formData.ai_provider === 'ollama'" text type="primary" size="small" @click="fetchOllamaModels()" :loading="loadingModels">
                  <template #icon><n-icon><refresh-outline /></n-icon></template>
                  {{ t('settings.refresh_models') }}
                </n-button>
              </n-space>
            </n-form-item>

            <n-form-item :label="t('settings.base_url')" path="ai_base_url">
              <n-input v-model:value="formData.ai_base_url" :placeholder="t('settings.base_url_placeholder')" />
            </n-form-item>
          </template>

          <n-space justify="end" style="margin-top: 24px">
            <n-button @click="testConnection" :loading="testing">
              <template #icon><n-icon><flash-outline /></n-icon></template>
              {{ t('settings.test_connection') }}
            </n-button>
            <n-button type="primary" @click="saveSettings" :loading="saving">
              <template #icon><n-icon><save-outline /></n-icon></template>
              {{ t('settings.save') }}
            </n-button>
          </n-space>
        </n-form>
      </n-card>

      <!-- Database Settings -->
      <n-card :title="t('settings.database')" class="settings-card glass-card">
        <n-descriptions bordered :column="1">
          <n-descriptions-item :label="t('settings.neo4j_uri')">{{ formData.neo4j_uri }}</n-descriptions-item>
          <n-descriptions-item :label="t('settings.neo4j_user')">{{ formData.neo4j_user }}</n-descriptions-item>
          <n-descriptions-item :label="t('settings.redis_url')">{{ formData.redis_url }}</n-descriptions-item>
        </n-descriptions>
        <n-alert type="info" style="margin-top: 16px">{{ t('settings.database_readonly_notice') }}</n-alert>
      </n-card>

      <!-- Help -->
      <n-card :title="t('settings.help')" class="settings-card glass-card">
        <n-collapse>
          <n-collapse-item :title="t('settings.supported_providers')" name="providers">
            <n-space vertical>
              <div v-for="p in allProviders" :key="p.id">
                <strong>{{ p.name }}</strong>
                <n-text depth="3" style="margin-left:8px">({{ t('settings.default_model') }}: {{ p.default_model }})</n-text>
                <n-tag v-if="p.requires_api_key" type="warning" size="small" style="margin-left:8px">{{ t('settings.api_key_required_tag') }}</n-tag>
              </div>
            </n-space>
          </n-collapse-item>
          <n-collapse-item :title="t('settings.how_to_use_ollama')" name="ollama">
            <n-ol><n-li>{{ t('settings.ollama_step1') }}</n-li><n-li>{{ t('settings.ollama_step2') }}</n-li><n-li>{{ t('settings.ollama_step3') }}</n-li></n-ol>
          </n-collapse-item>
          <n-collapse-item :title="t('settings.how_to_use_cloud_providers')" name="cloud">
            <n-space vertical>
              <div><strong>OpenAI / Anthropic / Google Gemini:</strong><n-ol><n-li>{{ t('settings.cloud_step1') }}</n-li><n-li>{{ t('settings.cloud_step2') }}</n-li><n-li>{{ t('settings.cloud_step3') }}</n-li></n-ol></div>
              <div><strong>{{ t('settings.chinese_providers') }}:</strong><n-ol><n-li>{{ t('settings.chinese_step1') }}</n-li><n-li>{{ t('settings.chinese_step2') }}</n-li></n-ol></div>
            </n-space>
          </n-collapse-item>
          <n-collapse-item :title="t('settings.configuration_tips')" name="tips">
            <n-ul><n-li>{{ t('settings.tip1') }}</n-li><n-li>{{ t('settings.tip2') }}</n-li><n-li>{{ t('settings.tip3') }}</n-li><n-li>{{ t('settings.tip4') }}</n-li></n-ul>
          </n-collapse-item>
        </n-collapse>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Settings.vue - AI Provider & System Settings View
 * AI 提供商与系统设置视图
 *
 * Purpose / 功能说明:
 *   Dynamic configuration form for AI providers (mock, OpenAI, Anthropic, Ollama, etc.).
 *   Provider-specific fields show/hide based on the selected provider type.
 *   Supports Ollama model fetching (via local API), connection testing,
 *   read-only display of database configuration (Neo4j, Redis), and
 *   collapsible help panels for provider setup guidance.
 *   用于 AI 提供商（mock、OpenAI、Anthropic、Ollama 等）的动态配置表单。
 *   根据选中的提供商类型显示/隐藏相应的字段。
 *   支持 Ollama 模型拉取（通过本地 API）、连接测试、
 *   数据库配置（Neo4j、Redis）的只读展示，以及可折叠的帮助面板。
 *
 * Data flow / 数据流:
 *   Load providers list (getAIProviders) -> Load saved settings (getSettings) ->
 *   User edits form -> Validate -> Save (updateAISettings) -> Reload settings ->
 *   Test connection (testAIConnection) with current values.
 *   加载提供商列表 -> 加载已保存设置 -> 用户编辑表单 -> 校验 -> 保存 -> 重新加载设置
 *   -> 使用当前值测试连接。
 */
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { FlashOutline, SaveOutline, RefreshOutline } from '@vicons/ionicons5'
import {
  getAIProviders,
  getSettings,
  updateAISettings,
  testAIConnection,
  getOllamaModels,
  type AIProvider,
  type Settings
} from '@/api/services'

const { t } = useI18n()
const message = useMessage()

// ---- Reactive State / 响应式状态 ----

/** Reference to the naive-ui form instance for validation / naive-ui 表单实例引用 */
const formRef = ref()

/** Form data model containing all AI and database settings / 包含所有 AI 和数据库设置的表单数据模型 */
const formData = ref<Settings>({
  ai_provider: 'mock',
  ai_api_key: '',
  ai_model: '',
  ai_base_url: '',
  neo4j_uri: '',
  neo4j_user: '',
  redis_url: ''
})

/** Whether settings are being saved / 设置是否正在保存 */
const saving = ref(false)
/** Whether a connection test is in progress / 连接测试是否在进行中 */
const testing = ref(false)
/** Whether Ollama models are being fetched / Ollama 模型是否正在拉取 */
const loadingModels = ref(false)
/** Whether the provider list is loading / 提供商列表是否正在加载 */
const loadingProviders = ref(false)

/** Full list of AI providers from the backend / 从后端获取的完整 AI 提供商列表 */
const allProviders = ref<AIProvider[]>([])
/** List of Ollama model names fetched from local Ollama API / 从本地 Ollama API 拉取的模型名称列表 */
const ollamaModels = ref<string[]>([])

// ---- Computed / 计算属性 ----

/** Provider options for the select dropdown / 提供商选择下拉框的选项 */
const providerOptions = computed(() => allProviders.value.map(p => ({ label: p.name, value: p.id })))

/** The currently selected AI provider object / 当前选中的 AI 提供商对象 */
const currentProvider = computed(() => allProviders.value.find(p => p.id === formData.value.ai_provider))

/** Ollama model options for the select dropdown / Ollama 模型选择下拉框的选项 */
const ollamaModelOptions = computed(() => ollamaModels.value.map(m => ({ label: m, value: m })))

/**
 * Dynamic form validation rules.
 * The API key is only required when the selected provider needs one.
 * 动态表单校验规则。API 密钥仅在选择需要它的提供商时为必填。
 */
const formRules = computed(() => ({
  ai_provider: { required: true, message: t('settings.provider_required'), trigger: 'change' },
  ai_api_key: {
    required: currentProvider.value?.requires_api_key,
    message: t('settings.api_key_required'),
    trigger: 'blur'
  }
}))

// ---- Data Loading Functions / 数据加载函数 ----

/**
 * Fetch the list of available AI providers from the backend.
 * 从后端获取可用 AI 提供商列表。
 */
const loadProviders = async () => {
  loadingProviders.value = true
  try {
    const r = await getAIProviders()
    if (r?.providers) allProviders.value = r.providers
  } catch { message.error(t('settings.load_providers_failed')) }
  finally { loadingProviders.value = false }
}

/**
 * Load saved settings from the backend.
 * If the API key is masked ("***"), clear it so the user can re-enter.
 * If the provider is Ollama, auto-fetch available models.
 * 从后端加载已保存的设置。
 * 如果 API 密钥被脱敏显示（"***"），则清除以便重新输入。
 * 如果提供商是 Ollama，自动拉取可用模型。
 */
const loadSettings = async () => {
  try {
    const r = await getSettings()
    if (r) {
      Object.assign(formData.value, r)
      // If the backend returns a masked API key, clear it so the user can re-enter
      // 如果后端返回了脱敏的 API 密钥，清空以便用户重新输入
      if (formData.value.ai_api_key === '***') formData.value.ai_api_key = ''
      if (formData.value.ai_provider === 'ollama') await fetchOllamaModels(true)
    }
  } catch { message.error(t('settings.load_failed')) }
}

// ---- Ollama-Specific Functions / Ollama 特有函数 ----

/**
 * Fetch Ollama models from the local Ollama API.
 * Preserves the currently selected model if it still exists in the fetched list.
 * When silent, no success/error toast is shown (used during initial load).
 * 从本地 Ollama API 拉取模型列表。
 * 如果当前选中的模型仍在列表中则保留选择。
 * 静默模式下不显示成功/错误提示（用于初始加载时）。
 */
const fetchOllamaModels = async (silent = false) => {
  loadingModels.value = true
  try {
    const r = await getOllamaModels()
    if (r.success) {
      const saved = formData.value.ai_model
      ollamaModels.value = r.models
      // If the previously selected model isn't in the list, append it to avoid losing it
      // 如果之前选中的模型不在列表中，追加回去以免丢失
      if (saved && !ollamaModels.value.includes(saved)) ollamaModels.value.push(saved)
      if (!silent) message.success(t('settings.models_loaded', { count: ollamaModels.value.length }))
    } else if (!silent) message.warning(r.message || t('settings.fetch_models_failed'))
  } catch { if (!silent) message.error(t('settings.fetch_models_failed')) }
  finally { loadingModels.value = false }
}

// ---- Event Handlers / 事件处理函数 ----

/**
 * Handle provider change: auto-fetch Ollama models if Ollama is selected,
 * and reset model/base_url fields for the new provider.
 * 处理提供商变更：如果选择了 Ollama 则自动拉取模型，
 * 并为新提供商重置 model/base_url 字段。
 */
const handleProviderChange = (v: string) => {
  if (v === 'ollama' && ollamaModels.value.length === 0) fetchOllamaModels()
  formData.value.ai_model = ''
  formData.value.ai_base_url = ''
}

/**
 * Test the AI connection with the current form values.
 * 使用当前表单值测试 AI 连接。
 */
const testConnection = async () => {
  testing.value = true
  try {
    const r = await testAIConnection(formData.value)
    r.success ? message.success(r.message) : message.error(r.message)
  } catch { message.error(t('settings.test_failed')) }
  finally { testing.value = false }
}

/**
 * Validate and save the settings form.
 * On success, reload settings to reflect the saved state.
 * 校验并保存设置表单。
 * 保存成功后重新加载设置以反映已保存的状态。
 */
const saveSettings = async () => {
  try {
    await formRef.value?.validate()
    saving.value = true
    const r = await updateAISettings(formData.value)
    r.success ? message.success(r.message) : message.error(r.message || t('settings.save_failed'))
    await loadSettings()
  } catch (e: any) { if (!e?.errors) message.error(t('settings.save_failed')) }
  finally { saving.value = false }
}

// ---- Lifecycle / 生命周期 ----

/** On mount, load providers and settings in sequence / 挂载时依次加载提供商列表和设置 */
onMounted(async () => { await loadProviders(); await loadSettings() })
</script>

<style lang="scss" scoped>
.settings-view {
  padding: 28px 40px; min-height: 100%; position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at 20% 20%, rgba(155,135,245,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(194,164,116,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.settings-container { max-width: 880px; margin: 0 auto; }

.settings-header {
  margin-bottom: 24px; padding: 24px 32px;
  .title { font-size: 30px; font-weight: 800; margin: 0 0 6px; }
  .subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
}

.settings-card {
  margin-bottom: 24px;
  :deep(.n-card-header) { font-weight: 700; font-size: 17px; }
}

:deep(.n-form-item-label) { font-weight: 600; }
:deep(.n-alert) { border-radius: var(--radius-md); }
</style>
