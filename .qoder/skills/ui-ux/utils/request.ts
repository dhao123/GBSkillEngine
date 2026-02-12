/**
 * HTTP请求工具
 * 
 * 封装fetch API，提供统一的请求处理、错误处理和认证
 */

import { Modal } from 'antd';

import type { ApiResponse, RequestOptions } from '../types/common';

import { getItem } from './storage';

/**
 * 处理错误响应
 */
function handleErrorResponse(data: unknown): void {
  const title = '请求失败';
  const content = (data as { message: string }).message || '服务器返回错误，请稍后再试';
  Modal.error({
    content,
    title,
  });
  throw new Error(`HTTP error! message: ${content}`);
}

/**
 * HTTP请求函数
 * 
 * @example
 * ```tsx
 * import request from '@/utils/request';
 * 
 * // GET 请求
 * const data = await request<User>('/api/user');
 * 
 * // POST 请求
 * const result = await request('/api/user', {
 *   method: 'POST',
 *   body: { name: 'test' }
 * });
 * 
 * // 带参数的 GET 请求
 * const list = await request('/api/users', {
 *   params: { page: '1', size: '10' }
 * });
 * ```
 * 
 * @param url 请求URL
 * @param options 请求配置
 * @returns 响应数据
 */
async function request<T = unknown, U = unknown>(
  url: string,
  options: RequestOptions<U> = {},
): Promise<T> {
  const { body, headers = {}, method = 'GET', params } = options;

  const queryString = params ? `?${new URLSearchParams(params).toString()}` : '';
  const newUrl = `${url}${queryString}`;
  const accessToken = getItem('access_token');
  const baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  if (accessToken) {
    baseHeaders.Authorization = `Bearer ${accessToken}`;
  }
  if (body && body instanceof FormData) {
    delete baseHeaders['Content-Type'];
  }
  const config: RequestInit = {
    headers: baseHeaders,
    method,
  };
  if (body) {
    config.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  try {
    const response = await fetch(newUrl, config);
    
    // 处理 401 未认证
    if (response.status === 401) {
      const loginUrl = `/api-auth/login?returnUrl=${encodeURIComponent(location.href)}`;
      globalThis.location.replace(loginUrl);
      throw new Error('Unauthorized');
    }
    
    // 处理不同响应类型
    switch (options.responseType) {
      case 'arraybuffer': {
        const arrayBufferData = await response.arrayBuffer();
        return arrayBufferData as unknown as T;
      }
      case 'blob': {
        const blobData = await response.blob();
        return blobData as unknown as T;
      }
      case 'text': {
        const textData = await response.text();
        return textData as unknown as T;
      }
    }
    
    const data = (await response.json()) as unknown as ApiResponse | null;
    
    // 处理返回数据
    if (!options.rawResponse && typeof data === 'object' && data !== null) {
      // 处理自研模块的返回格式
      if ('result' in data) {
        if ('success' in data && data.success) {
          return (data as { result: T }).result;
        } else {
          // 特殊状态码处理
          if (data.code === 409) {
            return data as T;
          }
          handleErrorResponse(data);
        }
      } else if ('data' in data) {
        // 处理其他格式的返回
        if (data.code === 0) {
          return (data as { data: T }).data;
        } else {
          handleErrorResponse(data);
        }
      }
    }

    return data as T;
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
}

export default request;
