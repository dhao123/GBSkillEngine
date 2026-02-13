import axios, { AxiosInstance, AxiosResponse } from 'axios'

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 响应拦截器 - 直接返回 data
api.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// 类型安全的请求封装
const request = {
  get: <T>(url: string, params?: Record<string, unknown>): Promise<T> =>
    api.get(url, { params }) as Promise<T>,
  post: <T>(url: string, data?: unknown, config?: Record<string, unknown>): Promise<T> =>
    api.post(url, data, config) as Promise<T>,
  put: <T>(url: string, data?: unknown): Promise<T> =>
    api.put(url, data) as Promise<T>,
  delete: <T>(url: string): Promise<T> =>
    api.delete(url) as Promise<T>,
}

export default request

// 国标相关API
export const standardsApi = {
  list: <T = unknown>(params?: Record<string, unknown>) => request.get<T>('/standards', params),
  detail: <T = unknown>(id: number) => request.get<T>(`/standards/${id}`),
  create: <T = unknown>(data: Record<string, unknown>) => request.post<T>('/standards', data),
  upload: <T = unknown>(formData: FormData) => 
    api.post('/standards/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }) as Promise<T>,
  update: <T = unknown>(id: number, data: Record<string, unknown>) => 
    request.put<T>(`/standards/${id}`, data),
  delete: <T = unknown>(id: number) => request.delete<T>(`/standards/${id}`),
  compile: <T = unknown>(id: number, options?: Record<string, unknown>) => 
    request.post<T>(`/standards/${id}/compile`, options || {}),
}

// Skill相关API
export const skillsApi = {
  list: <T = unknown>(params?: Record<string, unknown>) => request.get<T>('/skills', params),
  detail: <T = unknown>(skillId: string) => request.get<T>(`/skills/${skillId}`),
  create: <T = unknown>(data: Record<string, unknown>) => request.post<T>('/skills', data),
  update: <T = unknown>(skillId: string, data: Record<string, unknown>) => 
    request.put<T>(`/skills/${skillId}`, data),
  delete: <T = unknown>(skillId: string) => request.delete<T>(`/skills/${skillId}`),
  activate: <T = unknown>(skillId: string) => request.put<T>(`/skills/${skillId}/activate`),
  deactivate: <T = unknown>(skillId: string) => request.put<T>(`/skills/${skillId}/deactivate`),
  versions: <T = unknown>(skillId: string) => request.get<T>(`/skills/${skillId}/versions`),
}

// 物料梳理API
export const materialParseApi = {
  single: <T = unknown>(inputText: string) => 
    request.post<T>('/material-parse/single', { input_text: inputText }),
  batch: <T = unknown>(items: Array<{ id: number; inputText: string }>) => 
    request.post<T>('/material-parse/batch', { items }),
}

// 知识图谱API
export const knowledgeGraphApi = {
  visualize: <T = unknown>(params?: { centerNodeId?: string; depth?: number }) => 
    request.get<T>('/knowledge-graph/visualize', params as Record<string, unknown>),
  createNode: <T = unknown>(data: Record<string, unknown>) => 
    request.post<T>('/knowledge-graph/nodes', data),
  createRelationship: <T = unknown>(data: Record<string, unknown>) => 
    request.post<T>('/knowledge-graph/relationships', data),
  query: <T = unknown>(cypher: string, parameters?: Record<string, unknown>) => 
    request.post<T>('/knowledge-graph/query', { cypher, parameters }),
}

// 可观测API
export const observabilityApi = {
  executionLogs: <T = unknown>(params?: Record<string, unknown>) => 
    request.get<T>('/observability/execution-logs', params),
  traceDetail: <T = unknown>(traceId: string) => 
    request.get<T>(`/observability/execution-logs/${traceId}`),
  metrics: <T = unknown>() => request.get<T>('/observability/metrics'),
}

// 系统配置API
export const settingsApi = {
  // LLM配置
  getLLMConfigs: <T = unknown>() => request.get<T>('/settings/llm-configs'),
  getLLMConfig: <T = unknown>(id: number) => request.get<T>(`/settings/llm-configs/${id}`),
  createLLMConfig: <T = unknown>(data: Record<string, unknown>) => 
    request.post<T>('/settings/llm-configs', data),
  updateLLMConfig: <T = unknown>(id: number, data: Record<string, unknown>) => 
    request.put<T>(`/settings/llm-configs/${id}`, data),
  deleteLLMConfig: <T = unknown>(id: number) => 
    request.delete<T>(`/settings/llm-configs/${id}`),
  testConnection: <T = unknown>(id: number, testPrompt?: string) => 
    request.post<T>(`/settings/llm-configs/${id}/test`, { test_prompt: testPrompt }),
  setDefaultLLMConfig: <T = unknown>(id: number) => 
    request.put<T>(`/settings/llm-configs/${id}/set-default`),
  
  // 供应商信息
  getProviders: <T = unknown>() => request.get<T>('/settings/providers'),
  
  // 系统信息
  getSystemInfo: <T = unknown>() => request.get<T>('/settings/system-info'),

  // LLM使用监控
  getUsageMonitor: <T = unknown>(params?: { days?: number; provider?: string }) =>
    request.get<T>('/settings/llm-usage/monitor', params as Record<string, unknown>),
  getUsageLogs: <T = unknown>(params?: { skip?: number; limit?: number; provider?: string; success?: boolean }) =>
    request.get<T>('/settings/llm-usage/logs', params as Record<string, unknown>),
}
