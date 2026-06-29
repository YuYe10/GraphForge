<!--
  ============================================================================
  QADialog.vue — AI Question-Answer Dialog / AI 问答对话框
  ============================================================================
  Role:
    A modal dialog that provides an interactive Q&A interface backed by the
    knowledge graph's AI service. Users can ask natural-language questions,
    toggle knowledge-graph grounding, and receive answers with context
    references. Features include:
      - Conversation history with user/assistant message bubbles.
      - Streaming-like typing animation (three-dot loading indicator).
      - Markdown-to-HTML rendering for AI answers (bold, italic, code, lists).
      - Health check on open to display the active AI provider.
      - Collapsible context references showing the source snippets used.
      - Suggested questions for quick starts.

    一个模态对话框，提供基于知识图谱 AI 服务的交互式问答界面。用户可以
    提出自然语言问题、切换知识图谱引用开关，并接收带有上下文引用的答案。
    功能包括：
      - 带有用户/助手消息气泡的对话历史记录
      - 流式传输般的打字动画（三点加载指示器）
      - AI 答案的 Markdown 转 HTML 渲染（粗体、斜体、代码、列表）
      - 打开时进行健康检查以显示活跃的 AI 提供商
      - 可折叠的上下文引用，显示使用的源片段
      - 快速提问建议

  Design / 设计要点:
    - Uses v-model (`modelValue` / `update:modelValue`) for open/close control.
    - Implements a `ConversationMessage` interface extending the API's `Message`.
    - The `formatAnswer` function does basic Markdown rendering without
      introducing a full Markdown library dependency.
    - Context references are shown in a Naive UI Collapse component.
    ========================================================================
-->

<template>
  <!--
    Naive UI Modal / Naive UI 模态框
    - preset="card" gives the modal a card-like appearance.
    - @after-leave resets state when the modal finishes its close animation.
    - preset="card" 赋予模态框卡片式外观。
    - @after-leave 在模态框完成关闭动画时重置状态。
  -->
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
      <!--
        =====================================================================
        Messages area — displays the conversation or welcome state
        消息区域 — 显示对话或欢迎状态
        =====================================================================
      -->
      <div class="messages-area" ref="messagesContainerRef">
        <!--
          Welcome state — shown when there are no messages yet.
          欢迎状态 — 当还没有消息时显示。
         -->
        <div v-if="messages.length === 0" class="welcome-state">
          <div class="welcome-icon">
            <n-icon size="48"><chatbubble-outline /></n-icon>
          </div>
          <h3>开始提问以获得回答</h3>
          <p>基于知识图谱的智能问答系统</p>
          <!--
            Suggested questions — clickable tags that auto-fill and submit.
            建议问题 — 可点击的标签，自动填充并提交。
          -->
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

        <!--
          Messages list — rendered once the user has asked at least one question.
          消息列表 — 用户提出至少一个问题后渲染。
        -->
        <div v-else class="messages-list">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message', `message-${msg.role}`]"
          >
            <!-- Avatar icon (user = person, assistant = sparkles) -->
            <div class="message-avatar" :class="msg.role">
              <n-icon size="18">
                <person-circle-outline v-if="msg.role === 'user'" />
                <sparkles-outline v-else />
              </n-icon>
            </div>
            <div class="message-bubble" :class="msg.role">
              <!--
                Assistant answers are rendered as HTML via formatAnswer.
                User messages are displayed as plain text.
                助手答案通过 formatAnswer 渲染为 HTML。
                用户消息以纯文本显示。
              -->
              <div v-if="msg.role === 'assistant'" class="answer-text" v-html="formatAnswer(msg.content)"></div>
              <div v-else class="user-text">{{ msg.content }}</div>

              <!--
                Context reference — a collapsible section showing source snippets
                from the knowledge graph that the AI used to formulate its answer.
                上下文引用 — 可折叠区域，显示 AI 用于制定答案的知识图谱源片段。
              -->
              <div v-if="msg.context" class="context-reference">
                <n-collapse>
                  <n-collapse-item title="📚 参考信息" name="context">
                    <div class="context-text">{{ msg.context }}</div>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </div>
          </div>

          <!--
            Loading indicator — three animated dots shown while waiting for
            the AI response.
            加载指示器 — 等待 AI 响应时显示的三个动画点。
          -->
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

      <!--
        =====================================================================
        Input area — question input with controls
        输入区域 — 带控制项的问题输入区
        =====================================================================
      -->
      <div class="input-area">
        <!-- Options row: KG toggle + clear button / 选项行：KG 切换 + 清空按钮 -->
        <div class="input-options">
          <n-checkbox v-model:checked="useKG" size="small">使用知识图谱</n-checkbox>
          <n-button v-if="messages.length > 0" type="error" text size="small" @click="clearMessages">清空对话</n-button>
        </div>
        <!-- Input row: textarea + send button / 输入行：文本域 + 发送按钮 -->
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
          <n-button
            type="primary"
            :loading="loading"
            :disabled="!inputQuestion.trim() || loading"
            @click="handleAsk"
            class="send-btn"
          >
            <template #icon><n-icon size="18"><send-outline /></n-icon></template>
          </n-button>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
/**
 * ============================================================================
 * QADialog — Script
 * ============================================================================
 *
 * Manages the complete Q&A lifecycle: health check on open, sending questions
 * with conversation history, receiving and rendering answers, and state reset
 * on close.
 *
 * 管理完整的问答生命周期：打开时的健康检查、发送带有对话历史的问题、
 * 接收和渲染答案，以及关闭时的状态重置。
 */

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

/**
 * @typedef {Object} ConversationMessage
 * @property {'user'|'assistant'} role      - Who sent the message / 谁发送的消息
 * @property {string}             content   - Message body / 消息正文
 * @property {string}             [context] - Optional knowledge-graph context snippet
 *                                            可选的知识图谱上下文片段
 *
 * Extends the API's `Message` type with an optional `context` field used
 * to display source references for AI answers.
 * 扩展了 API 的 `Message` 类型，添加了用于显示 AI 答案源引用的可选 `context` 字段。
 */
interface ConversationMessage extends Message { context?: string }

/**
 * Props / 属性
 * @property {boolean} [modelValue=false] - v-model binding for dialog visibility
 *                                          v-model 绑定，控制对话框可见性
 */
const props = withDefaults(defineProps<{ modelValue?: boolean }>(), { modelValue: false })

/**
 * Emits / 事件
 * - 'update:modelValue': Emitted when the dialog is shown/hidden (v-model support)
 *                        对话框显示/隐藏时触发（支持 v-model）
 */
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const message = useMessage()

// ---------------------------------------------------------------------------
// Template refs / 模板引用
// ---------------------------------------------------------------------------

/** Container ref for scrolling to bottom on new messages / 用于新消息时滚动到底部的容器引用 */
const messagesContainerRef = ref<HTMLElement>()

// ---------------------------------------------------------------------------
// Reactive state / 响应式状态
// ---------------------------------------------------------------------------

/**
 * Two-way computed for v-model:show on NModal.
 * Reads from `modelValue` prop, writes to `update:modelValue` emit.
 * NModal 上 v-model:show 的双向计算属性。
 * 从 `modelValue` prop 读取，写入 `update:modelValue` 事件。
 */
const show = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

/** Array of all conversation messages / 所有对话消息的数组 */
const messages = ref<ConversationMessage[]>([])

/** Current question being typed in the input / 当前在输入框中输入的问题 */
const inputQuestion = ref('')

/** Whether an AI request is in flight / AI 请求是否正在进行中 */
const loading = ref(false)

/** Whether to ground answers in the knowledge graph / 是否将答案锚定在知识图谱中 */
const useKG = ref(true)

/** Name of the active AI provider (e.g., "OpenAI", "Qwen", "Claude") / 活跃 AI 提供商名称 */
const providerName = ref('AI')

// ---------------------------------------------------------------------------
// Suggested questions for quick start / 快速开始的建议问题
// ---------------------------------------------------------------------------
const suggestedQuestions = ['知识图谱中有哪些主要概念？', '请介绍一下图谱的结构', '有哪些文档被处理了？']

// ---------------------------------------------------------------------------
// Watchers / 侦听器
// ---------------------------------------------------------------------------

/**
 * When the dialog opens (`show` becomes true), perform a health check to
 * determine the active AI provider and warn if the service is unavailable.
 *
 * 当对话框打开时（`show` 变为 true），执行健康检查以确定活跃的 AI
 * 提供商，并在服务不可用时发出警告。
 */
watch(() => show.value, async (v) => {
  if (v) await initializeQA()
})

// ---------------------------------------------------------------------------
// Methods / 方法
// ---------------------------------------------------------------------------

/**
 * Initializes the Q&A system by checking the backend health endpoint.
 * Updates the provider name display and warns about service unavailability.
 *
 * 通过检查后端健康端点来初始化问答系统。
 * 更新提供商名称显示，并在服务不可用时发出警告。
 *
 * Health response provider name mapping / 健康响应提供商名称映射:
 * - openai    -> OpenAI
 * - qwen      -> Qwen
 * - glm       -> 智谱GLM
 * - deepseek  -> DeepSeek
 * - anthropic -> Claude
 * - ollama    -> Ollama
 * - mock      -> 模拟
 */
async function initializeQA() {
  try {
    const health = await checkQAHealth()
    const m: Record<string, string> = {
      openai: 'OpenAI',
      qwen: 'Qwen',
      glm: '智谱GLM',
      deepseek: 'DeepSeek',
      anthropic: 'Claude',
      ollama: 'Ollama',
      mock: '模拟'
    }
    providerName.value = m[health.provider] || health.provider
    // If the service is not healthy, inform the user but keep the dialog open.
    // 如果服务不健康，通知用户但保持对话框打开。
    if (health.status !== 'healthy') {
      message.warning(`AI服务不可用 (${health.provider})`)
    }
  } catch {
    // Silently ignore health check failures; the user will see an error
    // when they try to submit a question.
    // 静默忽略健康检查失败；用户提交问题时将看到错误提示。
  }
}

/**
 * Sends the current question to the AI service and streams the response
 * into the conversation. Handles errors and maintains the message history.
 *
 * 将当前问题发送到 AI 服务并将响应注入对话。处理错误并维护消息历史。
 *
 * Flow / 流程:
 *   1. Validate input / 验证输入
 *   2. Push user message / 推送用户消息
 *   3. Build conversation history (excluding the latest user message) / 构建对话历史（排除最新用户消息）
 *   4. Call the API / 调用 API
 *   5. Push assistant response (or revert on error) / 推送助手响应（出错时回退）
 *   6. Scroll to bottom / 滚动到底部
 */
async function handleAsk() {
  // --- Input validation / 输入验证 ---
  const q = inputQuestion.value.trim()
  if (!q) {
    message.warning('请输入问题')
    return
  }

  try {
    loading.value = true

    // Add the user's question to the conversation.
    // 将用户的问题添加到对话中。
    messages.value.push({ role: 'user', content: q })

    // Build the conversation history array for the API, excluding the
    // most recent user message (which is sent as `question`).
    // 为 API 构建对话历史数组，排除最新的用户消息（作为 `question` 发送）。
    const history: Message[] = messages.value
      .filter(m => m.role)
      .map(m => ({ role: m.role as 'user' | 'assistant', content: m.content }))

    // Call the backend Q&A endpoint.
    // 调用后端问答接口。
    const resp = await askQuestion({
      question: q,
      conversation_history: history.slice(0, -1), // Exclude the just-pushed message / 排除刚推送的消息
      use_kg: useKG.value
    })

    if (resp.success) {
      // Push the assistant's answer with optional context snippet.
      // 推送助手的答案及可选的上下文片段。
      messages.value.push({
        role: 'assistant',
        content: resp.answer,
        context: resp.context_snippet
      })
    } else {
      // On API error, remove the user message and show the error.
      // API 出错时，移除用户消息并显示错误。
      message.error(resp.error || '获取答案失败')
      messages.value.pop()
    }

    // Clear the input and scroll to the latest message.
    // 清空输入并滚动到最新消息。
    inputQuestion.value = ''
    await nextTick()
    scrollToBottom()
  } catch {
    // Network or unexpected error — revert the user message.
    // 网络或意外错误 — 回退用户消息。
    message.error('请求失败')
    messages.value.pop()
  } finally {
    loading.value = false
  }
}

/**
 * Clears all messages and the current input (keeps the dialog open).
 * 清除所有消息和当前输入（保持对话框打开）。
 */
function clearMessages() {
  messages.value = []
  inputQuestion.value = ''
}

/**
 * Full reset of all conversational state — called when the modal's
 * after-leave transition completes.
 *
 * 完全重置所有对话状态 — 在模态框的 after-leave 过渡完成时调用。
 */
function resetModal() {
  messages.value = []
  inputQuestion.value = ''
  loading.value = false
}

/**
 * Scrolls the messages container to the bottom to show the latest content.
 * 将消息容器滚动到底部以显示最新内容。
 */
function scrollToBottom() {
  const el = document.querySelector('.messages-area')
  if (el) el.scrollTop = el.scrollHeight
}

/**
 * Performs basic Markdown-to-HTML rendering for AI answers.
 * This avoids requiring a full Markdown library while covering the most
 * common formatting patterns used in answers.
 *
 * 对 AI 答案执行基础的 Markdown 转 HTML 渲染。
 * 避免引入完整的 Markdown 库，同时涵盖答案中最常见的格式化模式。
 *
 * Supported syntax / 支持的语法:
 *   **bold**    -> <strong>bold</strong>
 *   *italic*    -> <em>italic</em>
 *   `code`      -> <code>code</code>
 *   newline     -> <br>
 *   - list item -> <li>list item</li> (wrapped in <ul>)
 *
 * @param {string} text - Raw answer text from the AI / AI 返回的原始答案文本
 * @returns {string} HTML-safe rendered string / HTML 安全的渲染字符串
 */
function formatAnswer(text: string): string {
  return text
    // Bold: **text** -> <strong>text</strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic: *text* -> <em>text</em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Inline code: `text` -> <code>text</code>
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Newlines -> <br> for HTML rendering
    .replace(/\n/g, '<br>')
    // List items: "- text" -> <li>text</li>
    .replace(/^- (.*?)$/gm, '<li>$1</li>')
    // Group consecutive <li> elements into a <ul>
    .replace(/(<li>.*?<\/li>[\n]?)+/gs, '<ul>$&</ul>')
}
</script>

<style scoped>
// ==========================================================================
// QA Dialog Styles / 问答对话框样式
// ==========================================================================

.qa-container {
  display: flex;
  flex-direction: column;
  height: 580px;
}

// --------------------------------------------------------------------------
// Messages area / 消息区域
// --------------------------------------------------------------------------
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, rgba(248,250,252,0.8), rgba(241,245,249,0.8));
  border: 1px solid var(--color-border-light);
  scroll-behavior: smooth;
}

// Welcome state (no messages yet) / 欢迎状态（尚无消息）
.welcome-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;

  .welcome-icon {
    color: var(--color-primary-light);
    margin-bottom: 16px;
    opacity: 0.6;
  }

  h3 {
    font-size: 18px;
    font-weight: 700;
    color: var(--color-text);
    margin: 0 0 8px;
  }

  p {
    font-size: 13px;
    color: var(--color-text-muted);
    margin: 0 0 16px;
  }

  .suggestions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
}

// Conversation messages / 对话消息
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.message {
  display: flex;
  gap: 10px;
  animation: msgSlideIn 0.35s ease-out both;

  // User messages are right-aligned (row-reverse) / 用户消息右对齐
  &.message-user { flex-direction: row-reverse; }
  // Loading indicator is left-aligned / 加载指示器左对齐
  &.message-loading { flex-direction: row; }
}

// Role-based avatar styling / 基于角色的头像样式
.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.user {
    background: linear-gradient(135deg, #d4af37, #b8860b);
    color: #fff;
  }

  &.assistant {
    background: linear-gradient(135deg, #9b87f5, #7c6ae0);
    color: #fff;
  }
}

// Message bubble / 消息气泡
.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  word-break: break-word;
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

  // Three-dot thinking animation / 三点思考动画
  &.thinking {
    display: flex;
    gap: 4px;
    padding: 10px 20px;

    .thinking-dot {
      color: var(--color-text-muted);
      font-size: 10px;
      animation: dotBounce 1.4s ease-in-out infinite;

      // Staggered delays for a wave effect / 错位延迟以实现波浪效果
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
  }
}

// Rendered Markdown answer text / 渲染后的 Markdown 答案文本
.answer-text {
  line-height: 1.7;
  font-size: 14px;

  :deep(strong) {
    color: var(--color-primary-dark);
  }

  :deep(code) {
    background: rgba(194,164,116,0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--color-primary-dark);
  }

  :deep(ul) {
    margin: 6px 0;
    padding-left: 20px;
  }

  :deep(li) {
    margin: 3px 0;
  }
}

// Plain user text / 纯文本用户消息
.user-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}

// Collapsible context reference / 可折叠的上下文引用
.context-reference {
  margin-top: 10px;
  font-size: 12px;

  .context-text {
    max-height: 120px;
    overflow-y: auto;
    padding: 8px;
    background: rgba(194,164,116,0.04);
    border-radius: var(--radius-sm);
    font-family: var(--font-mono);
    white-space: pre-wrap;
    color: var(--color-text-muted);
  }
}

// --------------------------------------------------------------------------
// Input area / 输入区域
// --------------------------------------------------------------------------
.input-area {
  padding: 12px;
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-sm);

  .input-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }

  .question-input { flex: 1; }

  // Circular send button / 圆形发送按钮
  .send-btn {
    height: 40px;
    width: 40px;
    border-radius: 50% !important;
    flex-shrink: 0;
  }
}

// ==========================================================================
// Animations / 动画
// ==========================================================================

// Message slide-in from below / 消息从下方滑入
@keyframes msgSlideIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

// Three-dot bounce animation / 三点弹跳动画
@keyframes dotBounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-6px); }
}

// ==========================================================================
// Responsive / 响应式
// ==========================================================================
@media (max-width: 768px) {
  .qa-container { height: 480px; }
  .message-bubble { max-width: 85% !important; }
}
</style>
