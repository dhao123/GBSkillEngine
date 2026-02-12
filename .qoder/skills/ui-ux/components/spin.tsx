import type { SpinProps } from 'antd';
import { Icon } from '@iconify/react';

/**
 * 获取自定义加载图标
 * 使用 Iconify 私有化图标库中的动画图标
 */
export const getSpinIndicator = () => {
  return <Icon icon="@zkh:svg-spinners:blocks-shuffle-3" />;
};

/**
 * 获取完整的 Spin 配置
 * 
 * @param loading - 是否显示加载状态
 * @returns Spin 组件的 props
 * 
 * @example
 * ```tsx
 * // 在表格中使用
 * <Table loading={getSpinPros(loading)} {...props} />
 * 
 * // 在全局使用
 * import { getSpinIndicator } from '@/constants/spin';
 * <Spin indicator={getSpinIndicator()} spinning={loading}>
 *   {content}
 * </Spin>
 * ```
 */
export function getSpinPros(loading: boolean) {
  return {
    indicator: getSpinIndicator(),
    spinning: loading,
  } as SpinProps;
}
