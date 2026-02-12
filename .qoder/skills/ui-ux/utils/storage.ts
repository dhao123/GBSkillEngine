/**
 * 存储工具函数
 * 
 * 用于本地存储（localStorage）的读写操作
 */

import type { StorageKey } from '../types/common';

/**
 * 获取本地存储值
 * @param key 存储键名
 * @returns 存储的值
 */
export const getItem = (key: StorageKey): null | string => {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
};

/**
 * 设置本地存储值
 * @param key 存储键名
 * @param value 要存储的值
 */
export const setItem = (key: StorageKey, value: string): void => {
  try {
    localStorage.setItem(key, value);
  } catch {
    console.error('Failed to set item in localStorage');
  }
};

/**
 * 移除本地存储值
 * @param key 存储键名
 */
export const removeItem = (key: StorageKey): void => {
  try {
    localStorage.removeItem(key);
  } catch {
    console.error('Failed to remove item from localStorage');
  }
};

/**
 * 清空本地存储
 */
export const clearStorage = (): void => {
  try {
    localStorage.clear();
  } catch {
    console.error('Failed to clear localStorage');
  }
};
