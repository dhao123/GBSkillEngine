import { Icon } from '@iconify/react';
import { Dropdown } from 'antd';
import { useMemo } from 'react';
import { NavLink } from 'react-router';
import type { MenuProps } from 'antd';

/**
 * 用户信息类型
 */
export interface UserInfo {
  username: string;
  nickname?: string;
  avatar?: string;
}

/**
 * 工作空间类型
 */
export interface WorkSpace {
  id: string;
  name: string;
}

/**
 * Header菜单项类型
 */
export interface HeaderMenuItem {
  icon: string;
  link: string;
  title: string;
}

/**
 * Header模式
 */
export type HeaderMode = 'common' | 'simple';

/**
 * Header Props
 */
export interface HeaderProps {
  /**
   * 布局模式
   * - common: 完整布局（显示工作空间选择器）
   * - simple: 简化布局（仅显示Logo）
   */
  mode?: HeaderMode;
  /**
   * 用户信息
   */
  user?: UserInfo;
  /**
   * 当前工作空间
   */
  workspace?: WorkSpace;
  /**
   * 是否已登录
   */
  isLogin?: boolean;
  /**
   * 头部菜单项
   */
  headerMenu?: HeaderMenuItem[];
  /**
   * 工作空间选择器组件（可选）
   */
  WorkSpaceSelectComponent?: React.ComponentType<Record<string, unknown>>;
  /**
   * 登出回调
   */
  onLogout?: () => void;
  /**
   * Logo图片URL
   */
  logoUrl?: string;
  /**
   * 默认用户头像URL
   */
  defaultAvatarUrl?: string;
}

/**
 * Header - 头部导航组件
 * 
 * 顶部导航栏，包含Logo/工作空间选择器、导航菜单、用户信息和头像
 * 
 * @example
 * ```tsx
 * import Header from '@/components/Header';
 * 
 * <Header 
 *   mode="common"
 *   user={{ username: 'user@example.com', nickname: '测试者' }}
 *   isLogin={true}
 * />
 * ```
 */
// 默认占位图片（Base64 SVG）
const DEFAULT_LOGO = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjQwIiB2aWV3Qm94PSIwIDAgMTIwIDQwIiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMjAiIGhlaWdodD0iNDAiIHJ4PSI4IiBmaWxsPSIjRjBGMEYwIi8+PHRleHQgeD0iNjAiIHk9IjI1IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPkxPR088L3RleHQ+PC9zdmc+';
const DEFAULT_AVATAR = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzYiIGhlaWdodD0iMzYiIHZpZXdCb3g9IjAgMCAzNiAzNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxOCIgY3k9IjE4IiByPSIxOCIgZmlsbD0iI0UwRTBFMCIvPjxjaXJjbGUgY3g9IjE4IiBjeT0iMTQiIHI9IjYiIGZpbGw9IiM5OTkiLz48cGF0aCBkPSJNNiAzMmMwLTYuNjI3IDUuMzczLTEyIDEyLTEyczEyIDUuMzczIDEyIDEyIiBmaWxsPSIjOTk5Ii8+PC9zdmc+';

export function Header({
  mode = 'common',
  user,
  workspace,
  isLogin = false,
  headerMenu = [
    {
      icon: 'zkh:ai-dev:rili',
      link: 'https://aidev-docs.zkh360.com',
      title: '产品文档',
    },
  ],
  WorkSpaceSelectComponent,
  onLogout,
  logoUrl = DEFAULT_LOGO,
  defaultAvatarUrl = DEFAULT_AVATAR,
}: HeaderProps) {
  // 用户菜单项
  const dropdownItems: MenuProps['items'] = useMemo(() => {
    return [
      {
        key: '1',
        label: (
          <a
            href={`/api-auth/${isLogin ? 'logout' : 'login'}`}
            onClick={() => {
              if (isLogin && onLogout) {
                onLogout();
              }
            }}
            rel="noopener noreferrer">
            {isLogin ? '登出' : '登录'}
          </a>
        ),
      },
    ];
  }, [isLogin, onLogout]);

  return (
    <header className="h-[90px] px-[40px] flex flex-row items-center justify-between">
      {/* 左侧：Logo或工作空间选择器 */}
      <div>
        {mode === 'simple' ? (
          <NavLink className="h-[75px] flex items-center" to="/">
            <img alt="Logo" src={logoUrl} />
          </NavLink>
        ) : WorkSpaceSelectComponent ? (
          <WorkSpaceSelectComponent
            className="w-[260px]"
            defaultWorkSpace={workspace}
            style={{ height: '40px' }}
          />
        ) : (
          <NavLink className="h-[75px] flex items-center" to="/">
            <img alt="Logo" src={logoUrl} />
          </NavLink>
        )}
      </div>

      {/* 右侧：导航菜单 + 用户信息 */}
      <div className="flex-1 flex items-center justify-end">
        {/* 导航菜单 */}
        <div className="flex text-[14px] text-[#5F626D]">
          {headerMenu.map((item) => {
            return (
              <a
                className="mr-[40px] flex items-center"
                href={item.link}
                key={item.title}
                target="_blank"
                rel="noopener noreferrer">
                <Icon className="text-[16px]" icon={item.icon} />
                <span className="ml-[8px]">{item.title}</span>
              </a>
            );
          })}
        </div>

        {/* 用户信息 */}
        {user && (
          <>
            <div className="text-right mr-[15px]">
              <div className="text-[#333333] text-[14px] font-bold">
                {user.nickname || user.username}
              </div>
              <div className="text-[#666666] text-[12px] mt-[5px] font-normal">
                {user.username}
              </div>
            </div>

            {/* 用户头像下拉菜单 */}
            <Dropdown menu={{ items: dropdownItems }} placement="bottomRight">
              <img
                alt="User Avatar"
                className="w-[36px] h-[36px] cursor-pointer"
                src={user.avatar || defaultAvatarUrl}
              />
            </Dropdown>
          </>
        )}
      </div>
    </header>
  );
}

export default Header;
