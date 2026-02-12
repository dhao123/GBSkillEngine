/**
 * Spin 组件配置
 * 提供统一的加载指示器样式
 */
import type { SpinProps } from 'antd';

import { Icon } from '@iconify/react';

/**
 * 获取Spin加载指示器
 * 使用自定义动画图标
 */
export const getSpinIndicator = () => {
  return <Icon icon="@zkh:svg-spinners:blocks-shuffle-3" />;
};

/**
 * 获取Spin组件属性
 * @param loading - 是否显示加载状态
 * @returns SpinProps 配置对象
 */
export function getSpinPros(loading: boolean) {
  return {
    indicator: getSpinIndicator(),
    spinning: loading,
  } as SpinProps;
}
