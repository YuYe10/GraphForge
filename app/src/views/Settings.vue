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
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { FlashOutline, SaveOutline, RefreshOutline } from '@vicons/ionicons5'
import { getAIProviders, getSettings, updateAISettings, testAIConnection, getOllamaModels, type AIProvider, type Settings } from '@/api/services'

const { t } = useI18n()
const message = useMessage()

const formRef = ref()
const formData = ref<Settings>({ ai_provider: 'mock', ai_api_key: '', ai_model: '', ai_base_url: '', neo4j_uri: '', neo4j_user: '', redis_url: '' })
const saving = ref(false)
const testing = ref(false)
const loadingModels = ref(false)
const loadingProviders = ref(false)
const allProviders = ref<AIProvider[]>([])
const ollamaModels = ref<string[]>([])

const providerOptions = computed(() => allProviders.value.map(p => ({ label: p.name, value: p.id })))
const currentProvider = computed(() => allProviders.value.find(p => p.id === formData.value.ai_provider))
const ollamaModelOptions = computed(() => ollamaModels.value.map(m => ({ label: m, value: m })))
const formRules = computed(() => ({ ai_provider: { required: true, message: t('settings.provider_required'), trigger: 'change' }, ai_api_key: { required: currentProvider.value?.requires_api_key, message: t('settings.api_key_required'), trigger: 'blur' } }))

const loadProviders = async () => {
  loadingProviders.value = true
  try { const r = await getAIProviders(); if (r?.providers) allProviders.value = r.providers }
  catch { message.error(t('settings.load_providers_failed')) }
  finally { loadingProviders.value = false }
}

const loadSettings = async () => {
  try {
    const r = await getSettings()
    if (r) { Object.assign(formData.value, r); if (formData.value.ai_api_key === '***') formData.value.ai_api_key = ''; if (formData.value.ai_provider === 'ollama') await fetchOllamaModels(true) }
  } catch { message.error(t('settings.load_failed')) }
}

const fetchOllamaModels = async (silent = false) => {
  loadingModels.value = true
  try {
    const r = await getOllamaModels()
    if (r.success) {
      const saved = formData.value.ai_model
      ollamaModels.value = r.models
      if (saved && !ollamaModels.value.includes(saved)) ollamaModels.value.push(saved)
      if (!silent) message.success(t('settings.models_loaded', { count: ollamaModels.value.length }))
    } else if (!silent) message.warning(r.message || t('settings.fetch_models_failed'))
  } catch { if (!silent) message.error(t('settings.fetch_models_failed')) }
  finally { loadingModels.value = false }
}

const handleProviderChange = (v: string) => {
  if (v === 'ollama' && ollamaModels.value.length === 0) fetchOllamaModels()
  formData.value.ai_model = ''; formData.value.ai_base_url = ''
}

const testConnection = async () => {
  testing.value = true
  try { const r = await testAIConnection(formData.value); r.success ? message.success(r.message) : message.error(r.message) }
  catch { message.error(t('settings.test_failed')) }
  finally { testing.value = false }
}

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
