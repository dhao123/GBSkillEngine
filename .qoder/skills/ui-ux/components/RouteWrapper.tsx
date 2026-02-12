/**
 * RouteWrapper - 路由包装器组件
 * 使用 Suspense 包裹 Outlet，为懒加载路由提供 Loading 状态
 * 
 * @usage
 * 在路由配置中作为父路由的 element 使用
 * ```tsx
 * {
 *   path: '/application',
 *   element: <RouteWrapper />,
 *   children: [
 *     { path: 'dashboard', element: <Dashboard /> },
 *   ]
 * }
 * ```
 */
import { Suspense } from 'react';
import { Outlet } from 'react-router';

const RouteWrapper = () => {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Outlet />
    </Suspense>
  );
};

export default RouteWrapper;
