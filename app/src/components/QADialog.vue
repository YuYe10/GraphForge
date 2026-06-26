<template>
  <n-modal
    v-model:show="show"
    class="qa-modal"
    preset="card"
    :title="`💬 智能问答 — ${providerName}`"
    size="large"
    style="width: 750px; max-width: 95vw;"
    @after-leave="resetModal"
  >
    <div class="qa-container">
      <!-- Messages Area -->
      <div class="messages-area" ref="messagesContainerRef">
        <div v-if="messages.length === 0" class="welcome-state">
          <div class="welcome-icon">
            <n-icon size="48"><chatbubble-outline /></n-icon>
          </div>
          <h3>开始提问以获得回答</h3>
          <p>基于知识图谱的智能问答系统</p>
          <div class="suggestions">
            <n-tag
              v-for="q in suggestedQuestions"
              :key="q"
              :bordered="false"
              type="warning"
              size="small"
              style="cursor: pointer;"
              @click="inputQuestion = q; handleAsk()"
            >
              {{ q }}
            </n-tag>
          </div>
        </div>

        <div v-else class="messages-list">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', `message-${msg.role}`]"
          >
            <div class="message-avatar" :class="msg.role">
              <n-icon size="18">
                <person-circle-outline v-if="msg.role === 'user'" />
                <sparkles-outline v-else />
              </n-icon>
            </div>
            <div class="message-bubble" :class="msg.role">
              <div v-if="msg.role === 'assistant'" class="answer-text" v-html="formatAnswer(msg.content)"></div>
              <div v-else class="user-text">{{ msg.content }}</div>

              <!-- Context reference -->
              <div v-if="msg.context" class="context-reference">
                <n-collapse>
                  <n-collapse-item title="📚 参考信息" name="context">
                    <div class="context-text">{{ msg.context }}</div>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </div>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="message message-loading">
            <div class="message-avatar assistant">
              <n-icon size="18"><sparkles-outline /></n-icon>
            </div>
            <div class="message-bubble assistant thinking">
              <span class="thinking-dot">●</span>
              <span class="thinking-dot">●</span>
              <span class="thinking-dot">●</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <div class="input-options">
          <n-checkbox v-model:checked="useKG" size="small">使用知识图谱</n-checkbox>
          <n-button v-if="messages.length > 0" type="error" text size="small" @click="clearMessages">清空对话</n-button>
        </div>
        <div class="input-row">
          <n-input
            v-model:value="inputQuestion"
            type="textarea"
            placeholder="输入问题... (Ctrl+Enter 提交)"
            :rows="2"
            :disabled="loading"
            @keydown.ctrl.enter="handleAsk"
            @keydown.meta.enter="handleAsk"
            class="question-input"
          />
          <n-button type="primary" :loading="loading" :disabled="!inputQuestion.trim() || loading" @click="handleAsk" class="send-btn">
            <template #icon><n-icon size="18"><send-outline /></n-icon></template>
          </n-button>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import {
  NModal, NIcon, NInput, NButton,
  NCheckbox, NCollapse, NCollapseItem,
  NTag, useMessage
} from 'naive-ui'
import {
  ChatbubbleOutline, PersonCircleOutline, SparklesOutline, SendOutline
} from '@vicons/ionicons5'
import { askQuestion, checkQAHealth, type Message } from '@/api/services'

interface ConversationMessage extends Message { context?: string }

const props = withDefaults(defineProps<{ modelValue?: boolean }>(), { modelValue: false })
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const message = useMessage()
const messagesContainerRef = ref<HTMLElement>()

const show = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const messages = ref<ConversationMessage[]>([])
const inputQuestion = ref('')
const loading = ref(false)
const useKG = ref(true)
const providerName = ref('AI')

const suggestedQuestions = ['知识图谱中有哪些主要概念？', '请介绍一下图谱的结构', '有哪些文档被处理了？']

watch(() => show.value, async (v) => { if (v) await initializeQA() })

async function initializeQA() {
  try {
    const health = await checkQAHealth()
    const m: Record<string, string> = { openai: 'OpenAI', qwen: 'Qwen', glm: '智谱GLM', deepseek: 'DeepSeek', anthropic: 'Claude', ollama: 'Ollama', mock: '模拟' }
    providerName.value = m[health.provider] || health.provider
    if (health.status !== 'healthy') message.warning(`AI服务不可用 (${health.provider})`)
  } catch { /* silent */ }
}

async function handleAsk() {
  const q = inputQuestion.value.trim()
  if (!q) { message.warning('请输入问题'); return }
  try {
    loading.value = true
    messages.value.push({ role: 'user', content: q })
    const history: Message[] = messages.value.filter(m => m.role).map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))
    const resp = await askQuestion({ question: q, conversation_history: history.slice(0, -1), use_kg: useKG.value })
    if (resp.success) {
      messages.value.push({ role: 'assistant', content: resp.answer, context: resp.context_snippet })
    } else {
      message.error(resp.error || '获取答案失败')
      messages.value.pop()
    }
    inputQuestion.value = ''
    await nextTick(); scrollToBottom()
  } catch {
    message.error('请求失败'); messages.value.pop()
  } finally { loading.value = false }
}

function clearMessages() { messages.value = []; inputQuestion.value = '' }
function resetModal() { messages.value = []; inputQuestion.value = ''; loading.value = false }
function scrollToBottom() {
  const el = document.querySelector('.messages-area')
  if (el) el.scrollTop = el.scrollHeight
}

function formatAnswer(text: string): string {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
    .replace(/^- (.*?)$/gm, '<li>$1</li>')
    .replace(/(<li>.*?<\/li>[\n]?)+/gs, '<ul>$&</ul>')
}
</script>

<style scoped>
.qa-container { display: flex; flex-direction: column; height: 580px; }

.messages-area {
  flex: 1; overflow-y: auto; padding: 16px;
  margin-bottom: 12px; border-radius: var(--radius-xl);
  background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(241,245,249,0.8));
  border: 1px solid var(--color-border-light);
  scroll-behavior: smooth;
}

.welcome-state {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; text-align: center;
  .welcome-icon { color: var(--color-primary-light); margin-bottom: 16px; opacity: 0.6; }
  h3 { font-size: 18px; font-weight: 700; color: var(--color-text); margin: 0 0 8px; }
  p { font-size: 13px; color: var(--color-text-muted); margin: 0 0 16px; }
  .suggestions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
}

.messages-list { display: flex; flex-direction: column; gap: 14px; }

.message {
  display: flex; gap: 10px;
  animation: msgSlideIn 0.35s ease-out both;

  &.message-user { flex-direction: row-reverse; }
  &.message-loading { flex-direction: row; }
}

.message-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  &.user { background: linear-gradient(135deg, #d4af37, #b8860b); color: #fff; }
  &.assistant { background: linear-gradient(135deg, #9b87f5, #7c6ae0); color: #fff; }
}

.message-bubble {
  max-width: 75%; padding: 12px 16px;
  border-radius: var(--radius-lg); word-break: break-word;
  box-shadow: var(--shadow-sm);

  &.user {
    background: linear-gradient(135deg, rgba(212,175,55,0.15), rgba(185,134,11,0.15));
    border: 1px solid rgba(212,175,55,0.2);
    border-bottom-right-radius: 4px;
  }
  &.assistant {
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    border-bottom-left-radius: 4px;
  }
  &.thinking {
    display: flex; gap: 4px; padding: 10px 20px;
    .thinking-dot {
      color: var(--color-text-muted); font-size: 10px;
      animation: dotBounce 1.4s ease-in-out infinite;
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
  }
}

.answer-text {
  line-height: 1.7; font-size: 14px;
  :deep(strong) { color: var(--color-primary-dark); }
  :deep(code) { background: rgba(194,164,116,0.1); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 13px; color: var(--color-primary-dark); }
  :deep(ul) { margin: 6px 0; padding-left: 20px; }
  :deep(li) { margin: 3px 0; }
}

.user-text { font-size: 14px; line-height: 1.6; color: var(--color-text); }

.context-reference {
  margin-top: 10px; font-size: 12px;
  .context-text { max-height: 120px; overflow-y: auto; padding: 8px; background: rgba(194,164,116,0.04); border-radius: var(--radius-sm); font-family: var(--font-mono); white-space: pre-wrap; color: var(--color-text-muted); }
}

.input-area {
  padding: 12px; border-radius: var(--radius-xl);
  background: var(--color-surface); border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-sm);

  .input-options { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .input-row { display: flex; gap: 10px; align-items: flex-end; }
  .question-input { flex: 1; }
  .send-btn { height: 40px; width: 40px; border-radius: 50% !important; flex-shrink: 0; }
}

@keyframes msgSlideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes dotBounce { 0%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-6px); } }

@media (max-width: 768px) { .qa-container { height: 480px; } .message-bubble { max-width: 85% !important; } }
</style>
