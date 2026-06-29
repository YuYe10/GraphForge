/**
 * GraphForge API Client
 * ======================
 *
 * Core Axios HTTP client for the GraphForge frontend application.
 * Handles all communication with the backend FastAPI server, including
 * base URL configuration, request/response interceptors, and unified
 * error handling with Naive UI message integration.
 *
 * GraphForge 前端 API 客户端核心模块
 * 负责与后端 FastAPI 服务的所有通信，包括基础 URL 配置、
 * 请求/响应拦截器，以及与 Naive UI 消息系统集成的统一错误处理。
 */

import axios, { type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'

/**
 * Backend API base URL.
 *
 * Priority:
 *   1. Vite environment variable `VITE_API_BASE` (configured via .env file)
 *   2. Default fallback: `http://localhost:8000`
 *
 * 后端 API 基础地址，优先读取 Vite 环境变量，默认为本地开发地址。
 */
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

/**
 * Axios instance shared across all API service modules.
 *
 * Pre-configured with:
 * - Base URL pointing to the GraphForge backend
 * - 30-second request timeout
 * - JSON content type by default
 *
 * 全局 Axios 实例，预配置了后端地址、超时时间和默认请求头。
 */
const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// ---------------------------------------------------------------------------
// Request Interceptor
// 请求拦截器
// ---------------------------------------------------------------------------
/**
 * Attaches per-request transformations before the request is sent.
 *
 * Currently acts as a pass-through; can be extended to inject auth tokens,
 * CSRF headers, or request signing logic in the future.
 *
 * 在请求发送前执行，当前为透传。可在此注入认证令牌、CSRF 头或请求签名逻辑。
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// ---------------------------------------------------------------------------
// Response Interceptor
// 响应拦截器
// ---------------------------------------------------------------------------
/**
 * Processes all outgoing responses and handles errors uniformly.
 *
 * Success path:
 *   Unwraps the Axios response envelope so callers receive `response.data`
 *   directly, avoiding repetitive `.data` access in every service function.
 *
 *   Example: `api.get('/foo')` resolves to the server's JSON body, not the
 *   full Axios response object.
 *
 * Error path:
 *   Extracts the most relevant error message from the backend response.
 *   Resolution priority:
 *     1. `error.response.data.detail` — FastAPI validation/HTTPException detail
 *     2. `error.message`               — Generic Axios/network error message
 *     3. `'请求失败'`                   — Fallback Chinese placeholder
 *
 *   When a Naive UI `$message` global is available (registered in App.vue),
 *   the error is displayed as a toast notification. Otherwise it falls back
 *   to `console.error`.
 *
 * 统一处理响应与错误：
 * - 成功时自动解包，调用方直接获得 response.data
 * - 失败时提取最有用的错误信息，通过 Naive UI 消息组件提示用户
 */
api.interceptors.response.use(
  (response: AxiosResponse) => {
    // Unwrap Axios response envelope — return the server's JSON payload directly
    // 解包 Axios 响应，直接返回服务端 JSON 数据
    return response.data
  },
  (error) => {
    // -------------------------------------------------------------------
    // Error message resolution 错误消息提取优先级
    // -------------------------------------------------------------------
    // 1. FastAPI validation / HTTP exception detail field
    //    FastAPI 验证错误 / HTTPException 的 detail 字段
    // 2. Generic error message (network failure, timeout, etc.)
    //    通用错误信息（网络故障、超时等）
    // 3. Fallback Chinese placeholder  中文兜底提示
    // -------------------------------------------------------------------
    const message = error.response?.data?.detail || error.message || '请求失败'

    // Display error via Naive UI's global message API (injected in App.vue)
    // 通过 Naive UI 全局消息 API 显示错误（在 App.vue 中注册）
    if (window.$message) {
      window.$message.error(message)
    } else {
      console.error(message)
    }

    return Promise.reject(error)
  }
)

/**
 * Cancel an ongoing ingestion job.
 *
 * Sends a DELETE request to the backend's job cancellation endpoint.
 * Used to stop long-running document processing tasks (chunking, triplet
 * extraction, concept analysis).
 *
 * @param jobId - The unique identifier of the job to cancel / 待取消任务的唯一标识
 * @returns A promise resolving when the backend confirms cancellation
 *
 * 取消正在进行的导入任务，发送 DELETE 请求到后端取消接口。
 * 用于中止长耗时的文档处理任务（分块、三元组提取、概念分析）。
 */
export const cancelJob = (jobId: string) => {
  return api.delete(`/ingest/cancel/${jobId}`)
}

export default api
