# UI/UX Skill 组件库

本目录包含 AI 测试者平台 UI/UX Skill 的所有自定义组件代码。

## 📁 目录结构

```
skills/ui-ux/
├── assets/              # 图片资源
│   ├── logo.png                # Logo图标
│   ├── menuBg.png              # 侧边菜单背景图
│   ├── headerBg.png            # 头部背景图
│   ├── user.png                # 默认用户头像
│   └── banner/                 # Banner横幅图片
├── components/          # 自定义组件
│   ├── BaseTable.tsx           # 统一表格组件
│   ├── Tag.tsx                 # 自定义标签组件
│   ├── SliderInput.tsx         # 滑块输入组件
│   ├── spin.tsx                # 加载动画配置
│   ├── Banner.tsx              # 页面横幅组件
│   ├── BannerConstants.ts      # 横幅配置
│   ├── Nav.tsx                 # 侧边导航组件
│   ├── Header.tsx              # 头部导航组件
│   ├── Layout.tsx              # 布局组件
│   ├── RouteWrapper.tsx        # 路由包装器
│   ├── AuthWrapper.tsx         # 权限包装器
│   └── WorkSpaceSelect.tsx     # 工作空间选择器
├── core/                # 核心架构
│   └── context.ts              # 全局Context状态管理
├── constants/           # 常量配置
│   ├── index.ts                # 权限码、应用类型等
│   ├── menu.ts                 # 默认菜单配置
│   └── spin.tsx                # Spin加载图标
├── utils/               # 工具函数
│   ├── request.ts              # HTTP请求封装
│   ├── env.ts                  # 环境判断工具
│   ├── storage.ts              # 本地存储工具
│   └── channel.ts              # 跨Tab通信工具
├── hooks/               # 自定义 Hooks
│   └── useTitle.ts             # 页面标题管理
├── styles/              # 样式文件
│   └── global.css              # 全局样式
├── types/               # 类型定义
│   ├── common.ts               # 核心类型定义
│   └── assets.d.ts             # 图片资源类型声明
├── example/             # 示例代码
│   └── ExamplePage.tsx         # 示例页面
├── SKILL.md             # Skill 主文档
├── README.md            # 本文件
├── CHANGELOG.md         # 更新日志
└── package.json         # 依赖配置
```

## 🔧 组件说明

### BaseTable.tsx
统一的表格组件，封装了 Ant Design Table，提供：
- 统一的样式配置（大尺寸、居中对齐）
- 自动文本省略
- 统一的分页器
- 统一的加载动画

### Tag.tsx
轻量级标签组件，用于：
- 知识库标签展示
- 分类标记
- 状态标识

### SliderInput.tsx
滑块与数字输入组合组件，用于：
- 参数调整（相似度阈值、权重等）
- 模型配置
- 数值范围选择

### spin.tsx
统一的加载动画配置：
- 自定义 Iconify 图标
- 统一的 Spin 配置
- 用于全局加载和表格加载

### Banner.tsx & BannerConstants.ts
页面横幅组件及其配置：
- 功能模块入口页展示
- 教程链接入口
- 可配置的横幅内容
- 支持11种Banner类型（model、application、mcp等）

### Nav.tsx
侧边导航组件：
- 左侧固定宽度导航菜单
- 支持菜单分组和图标
- 自动高亮激活状态
- 支持外部链接跳转

### Header.tsx
头部导航组件：
- 顶部固定高度导航栏
- 支持Logo或工作空间选择器
- 用户信息展示和下拉菜单
- 支持simple和common两种模式

### Layout.tsx
布局容器组件：
- CommonLayout：完整布局（左侧导航 + 右侧内容）
- SimpleLayout：简化布局（仅Header + 内容）
- 支持路由权限验证
- 统一的页面结构和间距

### RouteWrapper.tsx
路由包装器：
- Suspense包装，支持懒加载
- 为懒加载路由提供Loading状态

### AuthWrapper.tsx
权限包装器：
- 统一处理按钮和功能的权限控制
- 根据权限码显示/隐藏子元素

### WorkSpaceSelect.tsx
工作空间选择器：
- 工作空间切换
- 申请加入空间
- 创建新空间
- 跨Tab同步

### useTitle Hook
页面标题管理 Hook：
- 从路由 handle 提取标题
- 自动拼接多级标题
- 统一的标题格式

## 🛠️ 核心架构

### Context 全局状态 (core/context.ts)
提供全局状态管理，包含：
- 用户信息 (user)
- 菜单列表 (menuList)
- 权限列表 (authList)
- 路由列表 (routerList)
- 默认工作空间 (defaultWorkSpace)
- 字典映射 (dictMap)

### 工具函数 (utils/)
- **request.ts**: HTTP请求封装，支持认证、错误处理、多种响应类型
- **env.ts**: 环境判断 (prod/gray/pre/daily/local)
- **storage.ts**: localStorage封装，支持token存取
- **channel.ts**: 跨Tab通信（BroadcastChannel API）

### 常量配置 (constants/)
- **index.ts**: 权限码映射、应用类型、默认图片等
- **menu.ts**: 默认菜单结构配置
- **spin.tsx**: 统一加载图标

### 类型定义 (types/)
- **common.ts**: 核心类型（User, Menu, WorkSpaceItem, AuthCode等）
- **assets.d.ts**: 图片资源类型声明

## 📦 依赖关系

```
Layout.tsx → Nav.tsx + Header.tsx + context.ts
Nav.tsx → assets/ (logo.png, menuBg.png)
Header.tsx → assets/ (logo.png, user.png)
Banner.tsx → BannerConstants.ts → assets/banner/*
BaseTable.tsx → spin.tsx → @iconify/react
SliderInput.tsx → antd (Slider, InputNumber)
useTitle.ts → react-router
AuthWrapper.tsx → context.ts + constants/
WorkSpaceSelect.tsx → request.ts + channel.ts
```

## 🚀 使用方式

### 1. 复制文件到项目

将整个 `skills/ui-ux/` 目录下的文件复制到项目对应目录：

```bash
# 复制所有组件
cp -r skills/ui-ux/components/* src/components/

# 复制 Hooks
cp -r skills/ui-ux/hooks/* src/hooks/

# 复制样式文件
cp -r skills/ui-ux/styles/* src/styles/

# 复制图片资源
cp -r skills/ui-ux/assets/* src/assets/

# 复制类型定义
cp -r skills/ui-ux/types/* src/types/

# 复制工具函数
cp -r skills/ui-ux/utils/* src/utils/

# 复制常量配置
cp -r skills/ui-ux/constants/* src/constants/

# 复制核心架构
cp -r skills/ui-ux/core/* src/core/
```

### 2. 引入全局样式

在项目入口文件（如 `main.tsx` 或 `index.tsx`）中引入全局样式：

```tsx
import './styles/global.css';
```

### 3. 安装依赖

```bash
pnpm add antd @iconify/react react-router
```

### 4. 在项目中使用

```tsx
// 使用完整布局
import Layout from '@/components/Layout';
import Banner from '@/components/Banner';

const menuList = [
  {
    name: '开发',
    children: [
      { name: '模型', icon: 'icon-moxing', link: '/model' },
      { name: '应用', icon: 'icon-yingyong', link: '/application' },
    ]
  }
];

const App = () => {
  return (
    <Layout
      mode="common"
      navProps={{ menuList }}
      headerProps={{ 
        user: { username: 'user@example.com', nickname: '测试者' },
        isLogin: true 
      }}
    >
      <Banner type="model" />
      {/* 页面内容 */}
    </Layout>
  );
};

// 使用 Nav 和 Header（自定义布局）
import Nav from '@/components/Nav';
import Header from '@/components/Header';

<div className="h-[100vh] flex">
  <div className="w-[180px] shrink-0">
    <Nav menuList={menuList} />
  </div>
  <div className="flex-1">
    <Header user={user} isLogin={true} />
    {/* 内容区域 */}
  </div>
</div>

// 使用 BaseTable
import BaseTable from '@/components/BaseTable';

<BaseTable
  columns={columns}
  dataSource={data}
  loading={loading}
/>

// 使用 Tag
import Tag from '@/components/Tag';

<Tag name="机器学习" id={1} />

// 使用 SliderInput
import SliderInput from '@/components/SliderInput';

<Form.Item label="阈值" name="threshold">
  <SliderInput min={0} max={1} step={0.01} />
</Form.Item>

// 使用 Banner
import Banner from '@/components/Banner';

<Banner type="model" />

// 使用 useTitle
import { useTitle } from '@/hooks/useTitle';

const title = useTitle();
```

## 📖 详细文档

完整的 UI/UX 设计规范和使用指南，请查看 [SKILL.md](./SKILL.md)

## 🔄 更新日志

### v2.1.0 (2026-01-27)
- ✨ 新增核心架构层 (core/context.ts)
- ✨ 新增工具函数 (utils/request, env, storage, channel)
- ✨ 新增常量配置 (constants/index, menu, spin)
- ✨ 新增业务组件 RouteWrapper, AuthWrapper, WorkSpaceSelect
- ✨ 新增核心类型定义 (types/common.ts)
- 📦 Layout 组件支持路由权限验证
- 📦 Layout 组件支持 useOutlet 和 enableAuth 配置
- 📦 完善背景图引用方式

### v2.0.0 (2026-01-27)
- ✨ 新增 Nav 侧边导航组件
- ✨ 新增 Header 头部导航组件
- ✨ 新增 Layout 布局组件（CommonLayout + SimpleLayout）
- ✨ 新增 global.css 全局样式文件
- ✨ 新增 assets 图片资源（logo、背景图、banner图等）
- ✨ 新增 assets.d.ts 图片资源类型声明
- 🐛 修复 Banner 组件图片引用路径
- 🐛 修复 Nav 激活状态样式问题
- ✨ BannerConstants 支持11种类型（新增 endpoint、plugins、observe、dataset、dimension、tasks）
- 📝 更新所有组件文档和使用说明

### v1.0.0 (2026-01-27)
- 初始版本
- 包含 6 个核心组件
- 包含 1 个自定义 Hook
- 完整的使用文档

---

**维护者**: AI Developer Platform Team  
**最后更新**: 2026-01-27
