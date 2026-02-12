import { useMatches } from 'react-router';

/**
 * useTitle - 页面标题管理 Hook
 * 
 * 从路由 handle 中提取标题并拼接
 * 
 * @returns 拼接后的页面标题，例如: "应用中心 - 应用详情"
 * 
 * @example
 * ```tsx
 * // 1. 在路由配置中设置 handle
 * {
 *   path: 'model/detail',
 *   Component: ModelDetail,
 *   handle: {
 *     title: '模型详情'
 *   }
 * }
 * 
 * // 2. 在组件中使用
 * import { useTitle } from '@/hooks/useTitle';
 * 
 * const Component = () => {
 *   const title = useTitle();
 *   
 *   useEffect(() => {
 *     if (title) {
 *       document.title = title;
 *     }
 *   }, [title]);
 *   
 *   return <div>{content}</div>;
 * };
 * ```
 */
export const useTitle = () => {
  const matches = useMatches();

  const title = matches
    .filter((match) => Boolean((match.handle as { title?: string })?.title))
    .map((match) => (match.handle as { title: string }).title)
    .join(' - ');

  return title || '智科汇AI测试者平台';
};
