import { Outlet, NavLink } from 'react-router-dom'
import {
  HomeOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  ApartmentOutlined,
  LineChartOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const menuItems = [
  { path: '/', icon: <HomeOutlined />, label: '首页' },
  { path: '/standards', icon: <FileTextOutlined />, label: '国标管理' },
  { path: '/skills', icon: <ThunderboltOutlined />, label: 'Skill管理' },
  { path: '/material-parse', icon: <ExperimentOutlined />, label: '物料梳理' },
  { path: '/knowledge-graph', icon: <ApartmentOutlined />, label: '知识图谱' },
  { path: '/observability', icon: <LineChartOutlined />, label: '执行日志' },
  { path: '/settings', icon: <SettingOutlined />, label: '系统配置' },
]

export default function Layout() {
  return (
    <div className="flex h-screen">
      {/* 侧边导航 */}
      <nav className="w-[200px] bg-white shadow-sm flex flex-col shrink-0">
        {/* Logo */}
        <div className="h-[60px] flex items-center justify-center border-b">
          <span className="text-xl font-bold brand-gradient-text">GBSkillEngine</span>
        </div>
        
        {/* 菜单 */}
        <div className="flex-1 py-4 overflow-y-auto">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center px-6 py-3 mx-2 rounded-lg text-[14px] transition-colors ${
                  isActive
                    ? 'bg-primary-light text-primary-dark font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <span className="text-[18px] mr-3">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
        
        {/* 底部信息 */}
        <div className="p-4 border-t text-center text-xs text-gray-400">
          MRO国标技能引擎平台
        </div>
      </nav>
      
      {/* 主内容区 */}
      <main className="flex-1 overflow-hidden bg-[#F1F3FA]">
        {/* 头部 */}
        <header className="h-[60px] bg-white shadow-sm flex items-center justify-between px-6">
          <div className="text-lg font-medium text-gray-700">
            国标 → Skill 编译 → 知识图谱 → 物料标准化梳理
          </div>
          <div className="text-sm text-gray-500">
            v1.0.0
          </div>
        </header>
        
        {/* 内容 */}
        <div className="p-6 h-[calc(100vh-60px)] overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
