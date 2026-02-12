/**
 * 核心类型定义
 * 
 * 项目中使用的通用类型定义
 */

import type { ReactNode } from 'react';

/**
 * 字典类型
 */
export interface Dict {
  displayName: string;
  domain: string;
  optionCode: string;
  typeCode: string;
  typeName: string;
}

export type DictMap = Record<string, Dict[] | null>;

/**
 * 菜单类型
 */
export interface Menu {
  antdIcon?: ReactNode;
  children?: Menu[];
  coding?: string;
  icon?: string;
  link?: string;
  name: string;
  type?: 'BUTTON' | 'MENU' | 'SERVICE';
}

export interface MenuInfo {
  children?: Menu[];
}

/**
 * 用户类型
 */
export interface User {
  email?: string;
  id: number;
  nickname?: string;
  phoneNum?: string;
  roleIds?: number[];
  username: string;
}

/**
 * 存储Key类型
 */
export type StorageKey = 'access_token' | 'refresh_token';
export type CookieKey = StorageKey;

/**
 * API响应类型
 */
export interface ApiResponse {
  code: number;
  message?: string;
}

/**
 * 页面横幅配置类型
 */
export interface PageHeaderBannerProps {
  /** banner背景图 */
  bannerBg: string;
  /** 描述 */
  description: string;
  /** 教程链接 */
  helperLink?: string;
  /** 教程文字 */
  helperText?: string;
  /** 是否需要展示【教程】模块 */
  needsHelper: boolean;
  /** 是否在新窗口打开链接 */
  openNewTab?: boolean;
  /** 标题 */
  title: string;
}

/**
 * 测试者用户类型
 */
export interface DevUser {
  nickname?: string;
  userName: string;
}

/**
 * 标签类型
 */
export interface Label {
  id: number;
  labelName: string;
}

/**
 * 工作空间类型
 */
export interface WorkSpaceItem {
  id: number;
  name: string;
  /** 1 管理员、2 成员 */
  perm?: number;
  permName?: string;
}

/**
 * 权限码类型
 */
export type AuthCode = string;

/**
 * HTTP请求方法
 */
export type HttpMethod = 'DELETE' | 'GET' | 'POST' | 'PUT';

/**
 * 请求配置
 */
export interface RequestOptions<T = unknown> {
  body?: T;
  headers?: Record<string, string>;
  method?: HttpMethod;
  params?: Record<string, string>;
  /** 是否不处理返回数据，默认处理 */
  rawResponse?: boolean;
  responseType?: 'arraybuffer' | 'blob' | 'json' | 'text';
}

/**
 * 环境类型
 */
export type Env = 'prod' | 'gray' | 'pre' | 'daily' | 'local';

/**
 * 应用类型
 */
export interface ApplicationType {
  bg: string;
  description: string;
  icon: string;
  label: string;
  value: string;
}
