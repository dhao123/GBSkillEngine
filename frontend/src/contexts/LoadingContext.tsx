/**
 * 全局Loading状态管理
 */
import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { Spin } from 'antd';

interface LoadingState {
  [key: string]: boolean;
}

interface LoadingContextType {
  // 检查某个key是否在加载中
  isLoading: (key: string) => boolean;
  // 检查是否有任何加载中的状态
  hasAnyLoading: boolean;
  // 开始加载
  startLoading: (key: string) => void;
  // 结束加载
  stopLoading: (key: string) => void;
  // 执行异步操作并自动管理loading状态
  withLoading: <T>(key: string, fn: () => Promise<T>) => Promise<T>;
}

const LoadingContext = createContext<LoadingContextType | undefined>(undefined);

interface LoadingProviderProps {
  children: React.ReactNode;
}

export const LoadingProvider: React.FC<LoadingProviderProps> = ({ children }) => {
  const [loadingState, setLoadingState] = useState<LoadingState>({});

  const isLoading = useCallback((key: string) => {
    return loadingState[key] ?? false;
  }, [loadingState]);

  const hasAnyLoading = useMemo(() => {
    return Object.values(loadingState).some(Boolean);
  }, [loadingState]);

  const startLoading = useCallback((key: string) => {
    setLoadingState(prev => ({ ...prev, [key]: true }));
  }, []);

  const stopLoading = useCallback((key: string) => {
    setLoadingState(prev => ({ ...prev, [key]: false }));
  }, []);

  const withLoading = useCallback(async <T,>(key: string, fn: () => Promise<T>): Promise<T> => {
    startLoading(key);
    try {
      const result = await fn();
      return result;
    } finally {
      stopLoading(key);
    }
  }, [startLoading, stopLoading]);

  const value = useMemo(() => ({
    isLoading,
    hasAnyLoading,
    startLoading,
    stopLoading,
    withLoading,
  }), [isLoading, hasAnyLoading, startLoading, stopLoading, withLoading]);

  return (
    <LoadingContext.Provider value={value}>
      {children}
    </LoadingContext.Provider>
  );
};

// Hook for using loading context
export const useLoading = () => {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within LoadingProvider');
  }
  return context;
};

// 全局Loading遮罩组件
interface GlobalLoadingProps {
  tip?: string;
}

export const GlobalLoading: React.FC<GlobalLoadingProps> = ({ tip = '加载中...' }) => {
  const { hasAnyLoading } = useLoading();

  if (!hasAnyLoading) {
    return null;
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.65)',
        zIndex: 9999,
      }}
    >
      <Spin size="large" tip={tip} />
    </div>
  );
};

// 预定义的Loading Keys
export const LoadingKeys = {
  // 页面级加载
  PAGE_INIT: 'page_init',
  PAGE_REFRESH: 'page_refresh',
  
  // 国标相关
  STANDARDS_LIST: 'standards_list',
  STANDARD_DETAIL: 'standard_detail',
  STANDARD_UPLOAD: 'standard_upload',
  STANDARD_COMPILE: 'standard_compile',
  
  // Skill相关
  SKILLS_LIST: 'skills_list',
  SKILL_DETAIL: 'skill_detail',
  SKILL_SAVE: 'skill_save',
  SKILL_TEST: 'skill_test',
  
  // 物料梳理
  MATERIAL_PARSE: 'material_parse',
  MATERIAL_BATCH: 'material_batch',
  MATERIAL_EXPORT: 'material_export',
  
  // 知识图谱
  GRAPH_LOAD: 'graph_load',
  GRAPH_SEARCH: 'graph_search',
  
  // 执行日志
  LOGS_LOAD: 'logs_load',
  LOGS_EXPORT: 'logs_export',
} as const;

export default LoadingContext;
