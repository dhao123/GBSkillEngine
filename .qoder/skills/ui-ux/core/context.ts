import { createContext } from 'react';

import type { AuthCode, DictMap, Menu, User, WorkSpaceItem } from '../types/common';

export type { AuthCode, Dict, DictMap, Menu, User, WorkSpaceItem } from '../types/common';

/**
 * Context 类型定义
 * 
 * 全局上下文，包含用户信息、权限列表、菜单列表、工作空间等
 */
export interface ContextType {
  /** 权限码列表 */
  authList: AuthCode[];
  /** 当前默认工作空间 */
  defaultWorkSpace: null | WorkSpaceItem;
  /** 字典数据 */
  dictMap: DictMap;
  /** 菜单列表 */
  menuList: Menu[];
  /** 铺平的有权限的路由数组集合 */
  routerList: string[];
  /** 当前用户信息 */
  user: null | User;
}

/**
 * CommonContext - 全局上下文
 * 
 * 用于在整个应用中共享用户信息、权限、菜单等数据
 * 
 * @example
 * ```tsx
 * // 在App组件中提供Context
 * import { CommonContext } from './context';
 * 
 * const App = () => {
 *   const contextValue = {
 *     authList: [],
 *     defaultWorkSpace: null,
 *     dictMap: {},
 *     menuList: [],
 *     routerList: [],
 *     user: null,
 *   };
 * 
 *   return (
 *     <CommonContext value={contextValue}>
 *       <RouterProvider router={router} />
 *     </CommonContext>
 *   );
 * };
 * 
 * // 在子组件中消费Context
 * import { use } from 'react';
 * import { CommonContext, type ContextType } from './context';
 * 
 * const Component = () => {
 *   const contextValue = use<ContextType>(CommonContext);
 *   return <div>{contextValue.user?.nickname}</div>;
 * };
 * ```
 */
export const CommonContext = createContext<ContextType>({
  authList: [],
  defaultWorkSpace: null,
  dictMap: {},
  menuList: [],
  routerList: [],
  user: null,
});

export default CommonContext;
