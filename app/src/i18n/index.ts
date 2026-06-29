/**
 * Internationalization (i18n) Setup / 国际化配置
 * ===============================================
 *
 * This module initializes vue-i18n with bilingual support (Chinese and English).
 * The locale is persisted in localStorage and falls back to Chinese when
 * the stored preference is unavailable or invalid.
 *
 * 本模块使用 vue-i18n 初始化双语支持（中文和英文）。
 * 语言偏好通过 localStorage 持久化存储，当存储的偏好不可用或无效时，
 * 默认回退到中文。
 *
 * Architecture / 架构说明:
 *   - Locale JSON files are co-located in ./locales/ for easy maintenance
 *     语言 JSON 文件位于 ./locales/ 目录下，便于维护
 *   - The MessageSchema type is inferred from zh.json, ensuring full type safety
 *     across the entire application when using t() in templates or scripts
 *     MessageSchema 类型从 zh.json 推断而来，确保整个应用中使用 t() 时具有完整的类型安全性
 *   - Locale switching is handled via appStore.setLanguage() and propagated
 *     by updating the reactive locale ref
 *     语言切换通过 appStore.setLanguage() 处理，并通过更新响应式 locale 引用传播
 *
 * Usage Example / 使用示例:
 *   import { useI18n } from 'vue-i18n'
 *   const { t, locale } = useI18n()
 *   // In template: {{ t('dashboard.title') }}
 *
 * Dependencies / 依赖:
 *   - vue-i18n ^9 (Composition API mode with legacy: false)
 *   - Locale JSON files: en.json, zh.json
 */

import { createI18n } from 'vue-i18n'
import zh from './locales/zh.json'
import en from './locales/en.json'

/**
 * MessageSchema type derived from the Chinese locale file.
 * 从中文语言文件推导出的消息结构类型。
 *
 * Using `typeof zh` as the schema type parameter ensures TypeScript
 * catches missing keys or incorrect nesting when calling t() throughout
 * the application. Both locale files should maintain identical structure.
 *
 * 使用 `typeof zh` 作为结构类型参数可确保 TypeScript 在整个应用
 * 调用 t() 时捕获缺失的键或错误的嵌套结构。两个语言文件应保持完全一致的结构。
 */
export type MessageSchema = typeof zh

/**
 * Message dictionary containing both locale bundles.
 * 包含两种语言包的消息字典。
 */
const messages = {
  zh,
  en,
}

/**
 * vue-i18n instance.
 *
 * Configuration / 配置说明:
 *   - legacy: false    — Enables Composition API mode (required for Vue 3) / 启用组合式 API 模式
 *   - locale           — Read from localStorage first; falls back to 'zh' / 优先从 localStorage 读取，回退到 'zh'
 *   - fallbackLocale   — When a key is missing in the active locale, fall back to 'zh' / 活动语言缺少键时回退到中文
 *   - messages         — The two locale dictionaries / 两种语言的消息字典
 *
 * The i18n instance is typed with the MessageSchema and supported locales,
 * providing compile-time safety for all translation lookups.
 * i18n 实例使用 MessageSchema 和受支持的语言进行类型化，
 * 为所有翻译查找提供编译时安全。
 */
const i18n = createI18n<[MessageSchema], 'zh' | 'en'>({
  legacy: false,
  locale: localStorage.getItem('language') || 'zh',
  fallbackLocale: 'zh',
  messages,
})

export default i18n
