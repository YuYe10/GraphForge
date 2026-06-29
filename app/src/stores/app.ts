/**
 * GraphForge — App Store (Pinia)
 * GraphForge — 应用状态存储 (Pinia)
 *
 * Manages global application-level state: the currently active UI language
 * (persisted in localStorage) and a global loading flag. The language toggle
 * action synchronises between the Pinia reactive ref, the vue-i18n locale,
 * and localStorage so the choice survives page reloads.
 *
 * 管理全局应用级状态：当前活跃的 UI 语言（持久化到 localStorage）
 * 以及全局加载标志。语言切换动作在 Pinia 响应式 ref、vue-i18n locale
 * 和 localStorage 三者之间同步，使语言选择在页面刷新后依然保留。
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import i18n from '@/i18n'

/**
 * Application-wide Pinia store.
 * 应用级 Pinia 状态存储。
 *
 * @returns {object} Reactive state and actions:
 *   - `language` — Current UI language ('zh' | 'en'), initialised from localStorage
 *                  当前 UI 语言，从 localStorage 初始化
 *   - `loading`   — Global loading indicator (e.g. for async operations overlay)
 *                   全局加载指示器（例如用于异步操作遮罩层）
 *   - `setLanguage` — Action to update language and persist the choice
 *                     更新语言并持久化选择的动作
 */
export const useAppStore = defineStore('app', () => {
  /**
   * Current UI language.
   * Initialised from localStorage with 'zh' as the fallback default.
   * 当前 UI 语言。从 localStorage 初始化，默认回退为 'zh'。
   */
  const language = ref<'zh' | 'en'>(
    localStorage.getItem('language') as 'zh' | 'en' || 'zh'
  )

  /**
   * Global loading flag. When `true`, UI components can display a loading
   * overlay or spinner to indicate an ongoing async operation.
   * 全局加载标志。当为 `true` 时，UI 组件可显示加载遮罩或旋转指示器。
   */
  const loading = ref<boolean>(false)

  /**
   * Set the UI language and persist the choice.
   * 设置 UI 语言并持久化选择。
   *
   * Performs three synchronisation steps:
   * 执行三个同步步骤：
   *   1. Updates the local reactive `language` ref
   *      更新本地响应式 `language` ref
   *   2. Assigns the value to vue-i18n's global locale so all translations
   *      re-evaluate immediately
   *      赋值给 vue-i18n 的全局 locale，使所有翻译立即重新求值
   *   3. Writes to localStorage so the preference survives page reloads
   *      写入 localStorage，使偏好设置可在页面刷新后保留
   *
   * @param lang — Target language code: 'zh' for Chinese, 'en' for English
   *               目标语言代码：'zh' 表示中文，'en' 表示英文
   */
  const setLanguage = (lang: 'zh' | 'en') => {
    language.value = lang
    // vue-i18n v9+ uses a Composer where `locale` is a Ref<string>;
    // vue-i18n v8 may expose it as a plain string.  A type cast to `any`
    // avoids version-specific type errors.
    // vue-i18n v9+ 中 `locale` 是 Ref<string>，而 v8 可能是普通字符串，
    // 使用 `any` 类型转换以避免版本相关的类型错误。
    ;(i18n.global as any).locale = lang
    localStorage.setItem('language', lang)
  }

  return {
    language,
    loading,
    setLanguage
  }
})
