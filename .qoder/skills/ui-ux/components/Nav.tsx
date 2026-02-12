import { Icon } from '@iconify/react';
import { useMemo } from 'react';
import { NavLink } from 'react-router';

import Logo from '../assets/logo.png';
import MenuBg from '../assets/menuBg.png';

/**
 * 菜单项类型
 */
export interface MenuItem {
  name: string;
  link?: string;
  icon?: string;
  children?: MenuItem[];
}

/**
 * 菜单分组类型
 */
export interface MenuGroup {
  name: string;
  children: MenuItem[];
}

/**
 * Nav Props
 */
export interface NavProps {
  /**
   * 菜单列表
   */
  menuList?: MenuGroup[];
  /**
   * Logo点击跳转路径
   */
  logoLink?: string;
}

/**
 * 外部网站的打开新的tab窗口
 */
const targetType = (link?: string) => {
  return link &&
    (link.startsWith('http://') || link.startsWith('https://') || link.includes('open=true'))
    ? '_blank'
    : '_self';
};

/**
 * NavItem - 导航菜单项
 */
const NavItem = ({ icon, link, name }: MenuItem) => {
  const iconName =
    icon && !icon.includes(':') ? `zkh:ai-dev:${icon.split('icon-')[1]}` : (icon ?? '');

  return (
    <NavLink
      className={({ isActive, isPending, isTransitioning }) =>
        [
          isPending ? 'pending' : '',
          isActive ? 'active bg-[#676BEF] text-[#FFF]' : '',
          isTransitioning ? 'transitioning' : '',
        ].join(' ') + ' flex items-center h-[30px] px-[10px] leading-[30px] rounded-[5px]'
      }
      target={targetType(link)}
      to={link ?? ''}>
      {iconName && <Icon className="text-[16px] w-[16px]" icon={iconName} />}
      <span className="ml-[10px]">{name}</span>
    </NavLink>
  );
};

/**
 * Nav - 侧边导航组件
 * 
 * 左侧导航菜单，包含Logo、固定菜单项和动态菜单分组
 * 
 * @example
 * ```tsx
 * import Nav from '@/components/Nav';
 * 
 * const menuList = [
 *   {
 *     name: '开发',
 *     children: [
 *       { name: '模型', icon: 'icon-moxing', link: '/model' },
 *       { name: '应用', icon: 'icon-yingyong', link: '/application' },
 *     ]
 *   }
 * ];
 * 
 * <Nav menuList={menuList} logoLink="/" />
 * ```
 */
export function Nav({ menuList = [], logoLink = '/' }: NavProps) {
  const filteredMenuList = useMemo(() => {
    return menuList.filter((item) => item.children && item.children.length > 0);
  }, [menuList]);

  return (
    <nav
      className="bg-white h-full px-[12px] overflow-y-auto bg-cover"
      style={{ backgroundImage: `url(${MenuBg})` }}>
      {/* Logo */}
      <NavLink className="h-[75px] flex items-center" to={logoLink}>
        <img alt="Logo" src={Logo} />
      </NavLink>

      {/* 分割线 */}
      <div className="h-[1px] bg-[#D7DEF4] mb-[20px]"></div>

      {/* 固定菜单项 */}
      <div className="text-[14px] text-[#333]">
        <NavItem icon="icon-shouye1" link="/" name="首页" />
      </div>

      {/* 动态菜单分组 */}
      {filteredMenuList.map((group) => {
        return (
          <div key={group.name}>
            {/* 分组标题 */}
            <div className="px-[10px] mt-[26px] mb-[14px] text-[12px] text-[#9297A9]">
              {group.name}
            </div>

            {/* 菜单项 */}
            {(group.children ?? [])
              .filter(
                ({ icon = '', link = '' }) =>
                  (link.startsWith('https://') || !link.includes(':')) && icon,
              )
              .map((child) => {
                return (
                  <div className="text-[14px] text-[#333]" key={child.name}>
                    <NavItem icon={child.icon} link={child.link} name={child.name} />
                  </div>
                );
              })}
          </div>
        );
      })}
    </nav>
  );
}

export default Nav;
