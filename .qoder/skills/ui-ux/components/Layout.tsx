import type { ReactNode } from 'react';

import { use, useEffect } from 'react';
import { matchPath, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router';

import { CommonContext, type ContextType } from '../core/context';
import { useTitle } from '../hooks/useTitle';

import Header, { type HeaderProps } from './Header';
import Nav, { type NavProps } from './Nav';

import headerBg from '../assets/headerBg.png';

/**
 * Layout Props
 */
export interface LayoutProps {
  /**
   * 子组件内容（用于非路由模式）
   */
  children?: ReactNode;
  /**
   * 布局模式
   * - common: 完整布局（左侧导航 + 右侧内容）
   * - simple: 简化布局（仅Header + 内容）
   */
  mode?: 'common' | 'simple';
  /**
   * Nav组件配置
   */
  navProps?: NavProps;
  /**
   * Header组件配置
   */
  headerProps?: HeaderProps;
  /**
   * 是否使用路由Outlet（默认为true）
   */
  useOutlet?: boolean;
  /**
   * 是否启用权限验证（默认为true）
   */
  enableAuth?: boolean;
}

/**
 * CommonLayout - 完整布局
 * 
 * 左侧导航 + 右侧内容区（Header + 主体）
 * 支持路由权限验证
 */
export function CommonLayout({
  children,
  navProps,
  headerProps,
  useOutlet = true,
  enableAuth = true,
}: Omit<LayoutProps, 'mode'>) {
  const contextValue = use<ContextType>(CommonContext);
  const title = useTitle();
  const location = useLocation();
  const navigate = useNavigate();

  // 设置页面标题
  useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);

  // 处理用户通过拼接地址访问没权限的菜单拦截
  useEffect(() => {
    if (enableAuth && contextValue.user?.id) {
      const routerList = contextValue.routerList;
      const pathname = location.pathname;
      const found = routerList.find((item) => {
        const match = matchPath(item, pathname);
        return match != null;
      });
      if (!found) {
        void navigate('/no-auth', { replace: true });
      }
    }
  }, [enableAuth, navigate, location.pathname, contextValue.user, contextValue.routerList, location]);

  return (
    <div className="h-[100vh] flex">
      {/* 左侧导航 - 固定宽度 */}
      <div className="w-[180px] shrink-0">
        <Nav {...navProps} />
      </div>

      {/* 右侧内容区 - 自适应 */}
      <div 
        className="flex-1 w-full overflow-y-hidden overflow-x-auto min-w-[1260px] bg-[#F1F3FA] bg-no-repeat bg-contain"
        style={{ backgroundImage: `url(${headerBg})` }}
      >
        <Header mode="common" {...headerProps} />
        <div className="w-full px-[40px] pb-[20px] h-[calc(100vh-90px)] max-h-[calc(100vh-90px)]">
          <div className="h-full overflow-y-auto">
            {useOutlet ? <Outlet /> : children}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * SimpleLayout - 简化布局
 * 
 * 仅Header + 主体（无侧边导航）
 */
export function SimpleLayout({
  children,
  headerProps,
  useOutlet = true,
}: Omit<LayoutProps, 'mode' | 'navProps'>) {
  const title = useTitle();

  useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);

  return (
    <div 
      className="h-[100vh] overflow-y-hidden overflow-x-auto min-w-[1260px] bg-[#F1F3FA] bg-no-repeat bg-contain"
      style={{ backgroundImage: `url(${headerBg})` }}
    >
      <Header mode="simple" {...headerProps} />
      <div className="w-full px-[40px] pb-[20px] h-[calc(100vh-90px)] max-h-[calc(100vh-90px)]">
        <div className="h-full overflow-y-auto">
          {useOutlet ? <Outlet /> : children}
        </div>
      </div>
    </div>
  );
}

/**
 * Layout - 自动布局组件（基于路由参数）
 * 
 * 根据 URL 参数 nav=0 自动选择简化布局
 * 
 * @example
 * 在路由配置中作为根布局使用
 * ```tsx
 * {
 *   path: '/',
 *   element: <Layout />,
 *   children: [...]
 * }
 * ```
 */
export function Layout(props: LayoutProps) {
  const [params] = useSearchParams();
  const nav = params.get('nav');

  // 根据URL参数自动选择布局
  if (nav === '0') {
    return <SimpleLayout {...props} />;
  }

  return <CommonLayout {...props} />;
}

/**
 * ManualLayout - 手动模式布局组件
 * 
 * 通过 mode 属性手动选择布局模式
 * 
 * @example
 * ```tsx
 * // 完整布局
 * <ManualLayout 
 *   mode="common"
 *   navProps={{ menuList }}
 *   headerProps={{ user, isLogin: true }}
 *   useOutlet={false}
 * >
 *   <YourContent />
 * </ManualLayout>
 * 
 * // 简化布局
 * <ManualLayout 
 *   mode="simple"
 *   headerProps={{ user, isLogin: true }}
 *   useOutlet={false}
 * >
 *   <YourContent />
 * </ManualLayout>
 * ```
 */
export function ManualLayout({ mode = 'common', ...props }: LayoutProps) {
  if (mode === 'simple') {
    return <SimpleLayout {...props} />;
  }
  return <CommonLayout {...props} />;
}

export default Layout;
