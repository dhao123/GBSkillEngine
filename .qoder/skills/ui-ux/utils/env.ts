/**
 * 环境判断工具
 * 
 * 基于hostname判断当前运行环境
 */

import type { Env } from '../types/common';

/**
 * 获取当前环境
 * 
 * @example
 * ```tsx
 * import { getEnv } from '@/utils/env';
 * 
 * const env = getEnv();
 * if (env === 'prod') {
 *   // 生产环境逻辑
 * }
 * ```
 * 
 * @returns 当前环境标识
 * - prod: 线上环境
 * - gray: 灰度环境
 * - pre: 预发环境
 * - daily: 日常/测试环境
 * - local: 本地环境
 */
export const getEnv = (): Env => {
  const hostname = location.hostname;
  
  // 可根据实际项目域名进行配置
  if (hostname.includes('prod') || hostname === 'aidev.zkh360.com') {
    return 'prod';
  } else if (hostname.includes('gray')) {
    return 'gray';
  } else if (hostname.includes('pre')) {
    return 'pre';
  } else if (hostname.includes('uat') || hostname.includes('daily') || hostname === 'aidev-uat.zkh360.com') {
    return 'daily';
  }
  return 'local';
};

/**
 * 是否为生产环境
 */
export const isProd = (): boolean => getEnv() === 'prod';

/**
 * 是否为开发环境（local）
 */
export const isDev = (): boolean => getEnv() === 'local';

/**
 * 是否为测试环境（daily/uat）
 */
export const isTest = (): boolean => getEnv() === 'daily';
