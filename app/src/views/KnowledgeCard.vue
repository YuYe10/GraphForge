<template>
  <div class="knowledge-card-page">
    <div class="page-bg"></div>

    <n-space vertical :size="24">
      <!-- Header -->
      <div class="page-header glass-card">
        <div>
          <h1 class="page-title gradient-text-purple">{{ $t('knowledge_card.title') }}</h1>
          <p class="page-subtitle">{{ $t('knowledge_card.subtitle') }}</p>
        </div>
        <n-button type="primary" size="large" @click="showCreateModal = true">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          {{ $t('knowledge_card.create_card') }}
        </n-button>
      </div>

      <!-- Filters -->
      <n-card size="small">
        <n-space>
          <n-select v-model:value="filterDomain" :options="domainOptions" :placeholder="$t('knowledge_card.filter_by_domain')" clearable style="width: 200px" @update:value="loadCards" />
          <n-select v-model:value="filterCategory" :options="categoryOptions" :placeholder="$t('knowledge_card.filter_by_category')" clearable style="width: 200px" @update:value="loadCards" />
        </n-space>
      </n-card>

      <!-- Cards Grid -->
      <n-spin :show="loading">
        <n-empty v-if="!loading && cards.length === 0" :description="$t('knowledge_card.no_cards')" size="large" />

        <div v-else class="cards-grid">
          <div v-for="card in cards" :key="card.id" class="kc-card glass-card">
            <div class="kc-card-header">
              <h4>{{ card.name }}</h4>
              <n-space :size="6">
                <n-tag :type="getImportanceType(card.importance)" size="tiny" :bordered="false">
                  {{ $t(`knowledge_card.importance_${card.importance}`) }}
                </n-tag>
              </n-space>
            </div>

            <p class="kc-desc">{{ card.description || $t('knowledge_card.description_placeholder') }}</p>

            <div class="kc-tags">
              <n-tag v-if="card.domain" type="info" size="small">{{ card.domain }}</n-tag>
              <n-tag v-if="card.category" type="success" size="small">{{ card.category }}</n-tag>
              <n-tag v-for="t in card.tags?.slice(0, 3)" :key="t" :bordered="false" size="small">{{ t }}</n-tag>
            </div>

            <div class="kc-footer">
              <span class="kc-meta">{{ $t('knowledge_card.connections') }}: {{ card.connection_count }}</span>
              <span class="kc-meta">{{ formatDate(card.updated_at) }}</span>
              <n-space :size="4">
                <n-button text size="tiny" @click="viewCard(card)"><template #icon><n-icon><EyeOutline /></n-icon></template></n-button>
                <n-button text size="tiny" @click="editCard(card)"><template #icon><n-icon><CreateOutline /></n-icon></template></n-button>
                <n-button text size="tiny" type="error" @click="confirmDelete(card)"><template #icon><n-icon><TrashOutline /></n-icon></template></n-button>
              </n-space>
            </div>
          </div>
        </div>
      </n-spin>

      <!-- Total -->
      <n-card v-if="total > 0" size="small">
        <div class="total-info">{{ $t('knowledge_card.total_cards', { count: total }) }}</div>
      </n-card>
    </n-space>

    <!-- Edit Modal -->
    <n-modal v-model:show="showEditModalComputed" preset="card" :title="isEditing ? $t('knowledge_card.edit_card') : $t('knowledge_card.create_card')" style="width: 800px">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="top">
        <n-tabs type="line" animated>
          <n-tab-pane name="basic" :tab="$t('knowledge_card.basic_info')">
            <n-space vertical :size="14">
              <n-form-item :label="$t('knowledge_card.card_name')" path="name">
                <n-input v-model:value="formData.name" :placeholder="$t('knowledge_card.card_name_placeholder')" :disabled="isEditing" />
              </n-form-item>
              <n-form-item :label="$t('knowledge_card.description')">
                <n-input v-model:value="formData.description" type="textarea" :rows="3" :placeholder="$t('knowledge_card.description_placeholder')" />
              </n-form-item>
              <n-grid :cols="2" :x-gap="16">
                <n-grid-item><n-form-item :label="$t('knowledge_card.domain')"><n-input v-model:value="formData.domain" :placeholder="$t('knowledge_card.domain_placeholder')" /></n-form-item></n-grid-item>
                <n-grid-item><n-form-item :label="$t('knowledge_card.category')"><n-input v-model:value="formData.category" :placeholder="$t('knowledge_card.category_placeholder')" /></n-form-item></n-grid-item>
              </n-grid>
              <n-form-item :label="$t('knowledge_card.importance')">
                <n-radio-group v-model:value="formData.importance">
                  <n-space><n-radio value="low">{{ $t('knowledge_card.importance_low') }}</n-radio><n-radio value="medium">{{ $t('knowledge_card.importance_medium') }}</n-radio><n-radio value="high">{{ $t('knowledge_card.importance_high') }}</n-radio></n-space>
                </n-radio-group>
              </n-form-item>
            </n-space>
          </n-tab-pane>
          <n-tab-pane name="extra" :tab="$t('knowledge_card.additional_info')">
            <n-space vertical :size="14">
              <n-form-item :label="$t('knowledge_card.tags')"><n-dynamic-tags v-model:value="formData.tags" /></n-form-item>
              <n-form-item :label="$t('knowledge_card.aliases')"><n-dynamic-tags v-model:value="formData.aliases" /></n-form-item>
            </n-space>
          </n-tab-pane>
          <n-tab-pane name="relations" :tab="$t('knowledge_card.relationships')">
            <n-form-item :label="$t('knowledge_card.related_concepts')"><n-dynamic-tags v-model:value="formData.related_concepts" /></n-form-item>
          </n-tab-pane>
        </n-tabs>
      </n-form>
      <template #footer>
        <n-space justify="end"><n-button @click="closeEditModal">{{ $t('knowledge_card.cancel') }}</n-button><n-button type="primary" :loading="submitting" @click="handleSubmit">{{ isEditing ? $t('knowledge_card.update') : $t('knowledge_card.create') }}</n-button></n-space>
      </template>
    </n-modal>

    <!-- View Modal -->
    <n-modal v-model:show="showViewModal" preset="card" :title="viewingCard?.name" style="width: 700px">
      <n-descriptions v-if="viewingCard" :column="2" bordered>
        <n-descriptions-item :label="$t('knowledge_card.card_name')">{{ viewingCard.name }}</n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.importance')"><n-tag :type="getImportanceType(viewingCard.importance)">{{ $t(`knowledge_card.importance_${viewingCard.importance}`) }}</n-tag></n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.domain')">{{ viewingCard.domain || '-' }}</n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.category')">{{ viewingCard.category || '-' }}</n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.description')" :span="2">{{ viewingCard.description || '-' }}</n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.tags')" :span="2"><n-space v-if="viewingCard.tags?.length">{{ viewingCard.tags.map((t: string) => h('n-tag', {}, t)) }}</n-space><n-text v-else depth="3">-</n-text></n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.connections')">{{ viewingCard.connection_count }}</n-descriptions-item>
        <n-descriptions-item :label="$t('knowledge_card.created_at')">{{ formatDate(viewingCard.created_at) }}</n-descriptions-item>
      </n-descriptions>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
/**
 * KnowledgeCard.vue - Knowledge Card Management View
 * 知识卡片管理视图
 *
 * Purpose / 功能说明:
 *   Full CRUD for knowledge cards with modal-based create/edit/view workflows.
 *   Supports filtering by domain and category, dynamic tag inputs, multi-tab forms
 *   (basic info, additional info, relationships), and importance labeling.
 *   提供知识卡片的完整增删改查(CRUD)功能，支持基于领域和分类的筛选、
 *   动态标签输入、多标签页表单（基本信息、附加信息、关联关系）以及重要性标记。
 *
 * Lifecycle / 卡片管理生命周期:
 *   Load (onMounted) -> Filter (domain/category) -> View/Edit/Create (modal) -> Save -> Reload
 *   加载(onMounted) -> 筛选(domain/category) -> 查看/编辑/创建(modal) -> 保存 -> 重新加载
 */
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import api from '@/api'
import { AddOutline, CreateOutline, TrashOutline, EyeOutline } from '@vicons/ionicons5'

const { t } = useI18n()
const message = useMessage()
const dialog = useDialog()

// ---- Reactive State / 响应式状态 ----

/** All loaded knowledge cards / 所有已加载的知识卡片 */
const cards = ref<any[]>([])
/** Total count from the API response / API 返回的总数 */
const total = ref(0)
/** Whether the card list is loading / 卡片列表是否正在加载 */
const loading = ref(false)
/** Whether a create/update submission is in progress / 创建/更新提交是否进行中 */
const submitting = ref(false)

/** Filter dropdown: selected domain (null means "all") / 筛选下拉框：选中的领域（null表示"全部"） */
const filterDomain = ref<string | null>(null)
/** Filter dropdown: selected category (null means "all") / 筛选下拉框：选中的分类（null表示"全部"） */
const filterCategory = ref<string | null>(null)

/** Whether the "create" modal is visible / 创建弹窗是否可见 */
const showCreateModal = ref(false)
/** Whether the "update" modal is visible / 更新弹窗是否可见 */
const showUpdateModal = ref(false)
/** Whether the "view details" modal is visible / 查看详情弹窗是否可见 */
const showViewModal = ref(false)

/** True when updating an existing card (derived from showUpdateModal) / 是否处于编辑状态（由 showUpdateModal 派生） */
const isEditing = computed(() => showUpdateModal.value)

/**
 * Unified computed for the edit modal's v-model:show.
 * Merges create and update into one modal, closing either when the modal is dismissed.
 * 统一的编辑弹窗 v-model:show 计算属性。
 * 合并创建和更新弹窗为一个弹窗，关闭时同时重置两者。
 */
const showEditModalComputed = computed({
  get: () => showCreateModal.value || showUpdateModal.value,
  set: (v) => { if (!v) { showCreateModal.value = false; showUpdateModal.value = false } }
})

/** Reference to the naive-ui form instance for validation / naive-ui 表单实例引用（用于表单校验） */
const formRef = ref()

/** Form model bound to the edit/create modal / 编辑/创建弹窗中绑定的表单数据模型 */
const formData = reactive({
  name: '',
  description: '',
  domain: '',
  category: '',
  importance: 'medium',
  tags: [] as string[],
  aliases: [] as string[],
  related_concepts: [] as string[],
  attributes: {}
})

/** Form validation rules / 表单校验规则 */
const formRules = {
  name: [{ required: true, message: t('knowledge_card.card_name_required'), trigger: 'blur' }]
}

/** The card being viewed in the detail modal / 查看弹窗中正在展示的卡片 */
const viewingCard = ref<any>(null)
/** ID of the card being edited (null when creating) / 正在编辑的卡片 ID（创建时为 null） */
const editingCardId = ref<string | null>(null)

// ---- Computed / 计算属性 ----

/**
 * Domain filter options derived from loaded cards.
 * Includes an "All" option at the top.
 * 从已加载卡片中提取领域筛选选项，顶部包含"全部"选项。
 */
const domainOptions = computed(() => {
  const domains = new Set(cards.value.map(c => c.domain).filter(Boolean))
  return [{ label: t('knowledge_card.all'), value: null }, ...Array.from(domains).map(d => ({ label: d, value: d }))]
})

/**
 * Category filter options derived from loaded cards.
 * Includes an "All" option at the top.
 * 从已加载卡片中提取分类筛选选项，顶部包含"全部"选项。
 */
const categoryOptions = computed(() => {
  const cats = new Set(cards.value.map(c => c.category).filter(Boolean))
  return [{ label: t('knowledge_card.all'), value: null }, ...Array.from(cats).map(c => ({ label: c, value: c }))]
})

// ---- Functions / 函数 ----

/**
 * Fetch knowledge cards from the API, applying domain/category filters if set.
 * 从 API 获取知识卡片列表，应用已设置的领域/分类筛选条件。
 */
const loadCards = async () => {
  loading.value = true
  try {
    const params: any = { limit: 100 }
    if (filterDomain.value) params.domain = filterDomain.value
    if (filterCategory.value) params.category = filterCategory.value
    const resp = await api.get('/knowledge-cards', { params })
    const d: any = resp.data || resp
    cards.value = d.cards || []; total.value = d.total || 0
  } catch (e: any) { message.error(e.response?.data?.detail || t('knowledge_card.load_failed')) }
  finally { loading.value = false }
}

/**
 * Open the view detail modal for a card.
 * 打开查看卡片详情的弹窗。
 */
const viewCard = (c: any) => { viewingCard.value = c; showViewModal.value = true }

/**
 * Open the edit modal and populate the form with the selected card's data.
 * Shallow-copies array/object fields to avoid mutating the original.
 * 打开编辑弹窗并将表单填充为选中卡片的数据。
 * 对数组/对象字段进行浅拷贝以避免修改原始数据。
 */
const editCard = (c: any) => {
  editingCardId.value = c.id
  Object.assign(formData, {
    name: c.name,
    description: c.description || '',
    domain: c.domain || '',
    category: c.category || '',
    importance: c.importance || 'medium',
    tags: [...(c.tags || [])],
    aliases: [...(c.aliases || [])],
    related_concepts: [...(c.related_concepts || [])],
    attributes: { ...(c.attributes || {}) }
  })
  showUpdateModal.value = true
}

/**
 * Show a confirmation dialog and delete the card on positive click.
 * 弹出确认对话框，确认后删除卡片。
 */
const confirmDelete = (c: any) => {
  dialog.warning({
    title: t('knowledge_card.confirm_delete'),
    content: t('knowledge_card.confirm_delete_message', { name: c.name }),
    positiveText: t('knowledge_card.delete'),
    negativeText: t('knowledge_card.cancel'),
    onPositiveClick: async () => {
      try {
        await api.delete(`/knowledge-cards/${c.id}`)
        message.success(t('knowledge_card.delete_success'))
        await loadCards()
      } catch (e: any) {
        message.error(e.response?.data?.detail || t('knowledge_card.delete_failed'))
      }
    }
  })
}

/**
 * Handle form submission for both create and update.
 * Validates the form, sends the appropriate POST or PUT request, then reloads the list.
 * 处理创建和更新的表单提交。
 * 校验表单，发送相应的 POST 或 PUT 请求，然后重新加载卡片列表。
 */
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    const payload = {
      name: formData.name,
      description: formData.description || undefined,
      domain: formData.domain || undefined,
      category: formData.category || undefined,
      importance: formData.importance,
      tags: formData.tags,
      aliases: formData.aliases,
      related_concepts: formData.related_concepts,
      attributes: formData.attributes
    }
    if (isEditing.value) {
      await api.put(`/knowledge-cards/${editingCardId.value}`, payload)
      message.success(t('knowledge_card.update_success'))
    } else {
      await api.post('/knowledge-cards', payload)
      message.success(t('knowledge_card.create_success'))
    }
    closeEditModal()
    await loadCards()
  } catch (e: any) {
    if (!e?.errors) message.error(e.response?.data?.detail || (isEditing.value ? t('knowledge_card.update_failed') : t('knowledge_card.create_failed')))
  } finally { submitting.value = false }
}

/**
 * Close the edit/create modal and reset the form data to defaults.
 * 关闭编辑/创建弹窗并将表单数据重置为默认值。
 */
const closeEditModal = () => {
  showCreateModal.value = false
  showUpdateModal.value = false
  editingCardId.value = null
  formRef.value?.restoreValidation()
  Object.assign(formData, {
    name: '',
    description: '',
    domain: '',
    category: '',
    importance: 'medium',
    tags: [],
    aliases: [],
    related_concepts: [],
    attributes: {}
  })
}

/**
 * Map importance level string to naive-ui tag type.
 * 将重要性等级字符串映射到 naive-ui 标签类型。
 */
const getImportanceType = (i: string) => ({ low: 'default', medium: 'info', high: 'warning' } as any)[i] || 'default'

/**
 * Format a date string to a localized human-readable string.
 * 将日期字符串格式化为本地化可读字符串。
 */
const formatDate = (d: string | null) => !d ? '-' : new Date(d).toLocaleString()

// ---- Lifecycle / 生命周期 ----

/** Load cards on component mount / 组件挂载时加载卡片列表 */
onMounted(() => loadCards())
</script>

<style lang="scss" scoped>
.knowledge-card-page {
  padding: 28px 40px; min-height: calc(100vh - 64px); position: relative;

  .page-bg {
    position: fixed; inset: 0;
    background: radial-gradient(ellipse at 20% 20%, rgba(155,135,245,0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(194,164,116,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
  }

  > * { position: relative; z-index: 1; }
}

.page-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 24px 32px;

  .page-title { font-size: 30px; font-weight: 800; margin: 0 0 6px; }
  .page-subtitle { font-size: 14px; color: var(--color-text-muted); margin: 0; }
}

.cards-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 18px;
}

.kc-card {
  padding: 22px; display: flex; flex-direction: column; gap: 12px;
  transition: all var(--transition-base); cursor: pointer; border: 1px solid var(--color-border-light);

  &:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg), 0 0 24px var(--color-primary-glow); }
}

.kc-card-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  h4 { margin: 0; font-size: 16px; font-weight: 700; color: var(--color-text); }
}

.kc-desc { font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; margin: 0; }

.kc-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.kc-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: auto; padding-top: 12px; border-top: 1px solid var(--color-border-light);
}

.kc-meta { font-size: 12px; color: var(--color-text-muted); font-weight: 500; }

.total-info { text-align: center; font-weight: 600; color: var(--color-text-secondary); }
</style>
