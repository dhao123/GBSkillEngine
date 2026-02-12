# UI/UX For AI Developer Platform

> **适用场景**：AI测试者平台的UI/UX设计与实现，提供统一的设计规范、组件使用指南和交互模式最佳实践

---

## 📋 目录

1. [设计系统概览](#设计系统概览)
2. [色彩系统](#色彩系统)
3. [布局与间距](#布局与间距)
4. [组件规范](#组件规范)
5. [交互模式](#交互模式)
6. [响应式设计](#响应式设计)
7. [可访问性](#可访问性)
8. [最佳实践](#最佳实践)

---

## 设计系统概览

### 技术栈
- **UI框架**: Ant Design 6.1.1
- **样式方案**: TailwindCSS 4.1.18 + 自定义主题 + 全局样式
- **图标库**: @iconify/react 6.0.2 (私有化方案: zkh:ai-dev:*)
- **字体**: 系统字体 + 钉钉进步体
- **图片资源**: 内置Logo、背景图、Banner图等

### 设计原则
1. **一致性优先**: 统一的视觉语言和交互模式
2. **响应式友好**: 支持多屏幕尺寸，最小宽度1260px
3. **可访问性**: 语义化标签、键盘导航、屏幕阅读器支持
4. **性能优化**: 减少DOM节点、优化渲染、懒加载

### 资源文件说明

**全局样式文件**: `styles/global.css`
- 导航激活状态样式
- 滚动条美化
- Ant Design组件主题覆盖
- 通用工具类样式

**图片资源目录**: `assets/`
- `logo.png`: 平台Logo
- `menuBg.png`: 侧边菜单背景图
- `headerBg.png`: 头部背景图
- `user.png`: 默认用户头像
- `banner/`: Banner横幅图片集合（11种场景）

**类型声明文件**: `types/assets.d.ts`
- 图片资源TypeScript类型声明
- 支持.png、.jpg、.svg等格式

---

## 色彩系统

### 品牌色

```css
/* 主色调 - 品牌渐变色 */
--brand-gradient: linear-gradient(to right, #3462FE, #9D34FE);

/* 主色调 - 蓝紫色系 */
--primary-blue: #676BEF;      /* 主要交互色 */
--primary-purple: #4F4FF6;    /* 强调色 */
--primary-light: #E6E9FD;     /* 浅色背景 */

/* 辅助色 - 蓝色系 */
--info-blue: #5293FE;         /* 信息提示 */
--info-light: #E8EFFF;        /* 信息背景 */

/* 警告色 */
--warning-orange: #C0811D;    /* 警告文字 */
--warning-bg: #FED17D;        /* 警告背景 */

/* 危险色 */
--danger-red: #F35859;        /* 错误/危险 */
```

### 中性色

```css
/* 文字颜色 */
--text-primary: #333333;      /* 主要文字 */
--text-secondary: #545E74;    /* 次要文字 */
--text-tertiary: #5F626D;     /* 三级文字 */
--text-disabled: #666666;     /* 禁用文字 */
--text-placeholder: #9297A9;  /* 占位符 */

/* 背景颜色 */
--bg-page: #F1F3FA;           /* 页面背景 */
--bg-content: #FFFFFF;        /* 内容背景 */
--bg-light: #F5F7FF;          /* 浅色背景 */
--bg-hover: #F5F5F5;          /* 悬停背景 */

/* 边框颜色 */
--border-light: #D7DEF4;      /* 浅色边框 */
--border-primary: #8eb0f9;    /* 主要边框 */
```

### 色彩使用规范

**文字颜色层级**
- 一级标题/重要信息: `#333333`
- 二级标题/描述文字: `#545E74`
- 辅助信息/帮助文字: `#5F626D` / `#666666`
- 分组标题/占位符: `#9297A9`

**交互色使用**
- 主要按钮/重要操作: 品牌渐变色或 `#676BEF`
- 链接/可点击元素: `#4F4FF6`
- 悬停状态: 降低不透明度或背景色变化
- 选中状态: 使用品牌色高亮

---

## 布局与间距

### 页面布局

#### 1. CommonLayout (完整布局)
```tsx
// 结构：左侧导航 + 右侧内容区（Header + 主体）
<div className="h-[100vh] flex">
  {/* 左侧导航 - 固定宽度 */}
  <div className="w-[180px] shrink-0">
    <Nav />
  </div>
  
  {/* 右侧内容区 - 自适应 */}
  <div className="flex-1 w-full overflow-y-hidden overflow-x-auto min-w-[1260px] bg-[#F1F3FA]">
    <Header />
    <div className="w-full px-[40px] pb-[20px] h-[calc(100vh-90px)]">
      <div className="h-full overflow-y-auto">
        <Outlet />
      </div>
    </div>
  </div>
</div>
```

**关键尺寸**
- 左侧导航宽度: `180px`
- Header高度: `90px`
- 内容区左右内边距: `40px`
- 内容区底部内边距: `20px`
- 最小页面宽度: `1260px`

#### 2. SimpleLayout (简化布局)
```tsx
// 结构：仅Header + 主体（无侧边导航）
<div className="h-[100vh] overflow-y-hidden overflow-x-auto min-w-[1260px] bg-[#F1F3FA]">
  <Header mode="simple" />
  <div className="w-full px-[40px] pb-[20px] h-[calc(100vh-90px)]">
    <div className="h-full overflow-y-auto">
      <Outlet />
    </div>
  </div>
</div>
```

### 间距系统

**基础间距单位**: 4px (使用TailwindCSS间距单位)

**常用间距值**
```css
/* 小间距 */
gap-1: 4px    /* 紧密元素 */
gap-2: 8px    /* 图标与文字 */
gap-4: 16px   /* 表单项、按钮组 */

/* 中间距 */
gap-6: 24px   /* 卡片内容 */
gap-8: 32px   /* 模块间距 */
gap-10: 40px  /* 页面主要区块 */

/* 大间距 */
gap-15: 60px  /* 页面主要段落 */
gap-20: 80px  /* 页面顶部间距 */
```

**内边距规范**
- 页面容器: `px-[40px] pb-[20px]`
- 卡片/模块: `p-4` (16px) 或 `p-6` (24px)
- 表单内容: `p-4`
- 按钮内边距: 由Ant Design控制，特殊需求可覆盖

**外边距规范**
- 标题与内容: `mb-[15px]` 或 `mb-[20px]`
- 段落间距: `mb-[10px]` 或 `mb-4`
- 模块间距: `mb-[26px]` 或 `mt-[26px]`

### 内容宽度

**中心化内容宽度**
```tsx
// 首页等展示页面使用固定宽度居中
<div className="w-[1188px] mx-auto">
  {/* 内容 */}
</div>
```

**最小宽度约束**
```css
min-w-[1260px]  /* 防止内容过度压缩 */
```

---

## 组件规范

### Header (头部导航)

**结构**
```tsx
<header className="h-[90px] px-[40px] flex flex-row items-center justify-between">
  {/* 左侧：Logo或工作空间选择器 */}
  <div>
    {mode === 'simple' ? <Logo /> : <WorkSpaceSelect />}
  </div>
  
  {/* 右侧：导航菜单 + 用户信息 */}
  <div className="flex-1 flex items-center justify-end">
    <NavMenu />
    <UserInfo />
    <UserAvatar />
  </div>
</header>
```

**样式规范**
- 高度: `90px`
- 内边距: `px-[40px]`
- 背景: 透明，继承页面背景图
- 对齐: `items-center justify-between`

**菜单项样式**
```tsx
<a className="mr-[40px] flex items-center">
  <Icon className="text-[16px]" icon={item.icon} />
  <span className="ml-[8px]">{item.title}</span>
</a>
```

**用户信息样式**
```tsx
<div className="text-right mr-[15px]">
  <div className="text-[#333333] text-[14px] font-bold">
    {nickname}
  </div>
  <div className="text-[#666666] text-[12px] mt-[5px] font-normal">
    {username}
  </div>
</div>
```

### Nav (侧边菜单)

**结构**
```tsx
<nav className="bg-white h-full px-[12px] overflow-y-auto">
  {/* Logo区域 */}
  <div className="h-[75px] flex items-center">
    <Logo />
  </div>
  
  {/* 分割线 */}
  <div className="h-[1px] bg-[#D7DEF4] mb-[20px]"></div>
  
  {/* 固定菜单项 */}
  <NavItem icon="icon-shouye1" link="/" name="首页" />
  
  {/* 动态菜单分组 */}
  {menuList.map(group => (
    <div key={group.name}>
      <div className="px-[10px] mt-[26px] mb-[14px] text-[12px] text-[#9297A9]">
        {group.name}
      </div>
      {group.children.map(item => (
        <NavItem {...item} />
      ))}
    </div>
  ))}
</nav>
```

**样式规范**
- 宽度: `180px` (由布局控制)
- 内边距: `px-[12px]`
- 背景: 白色 + 背景图
- 滚动: `overflow-y-auto`

**菜单项样式**
```tsx
// 普通状态
<NavLink className="flex items-center h-[40px] px-[10px] rounded-[5px] text-[14px] text-[#333]">
  <Icon />
  <span>{name}</span>
</NavLink>

// 激活状态 (由NavLink自动添加active类)
.active {
  background-color: #E6E9FD;
  color: #4F4FF6;
}
```

**分组标题样式**
```css
text-[12px] text-[#9297A9] px-[10px] mt-[26px] mb-[14px]
```

### BaseTable (数据表格)

**使用方式**
```tsx
<BaseTable
  columns={columns}
  dataSource={dataSource}
  loading={loading}
  pagination={{
    current: page,
    pageSize: pageSize,
    total: total,
    onChange: handlePageChange
  }}
  rowKey="id"
  // 可选
  rowSelection={rowSelection}
  xScroll="max-content"
  bordered={false}
  size="large"
/>
```

**默认配置**
- `size`: `'large'` - 大尺寸行高
- `bordered`: `false` - 不显示边框
- `ellipsis`: `true` - 文本超出显示省略号
- `align`: `'center'` - 所有列居中对齐
- `showQuickJumper`: `true` - 显示快速跳转
- `showSizeChanger`: `true` - 显示每页条数选择器
- `showTotal`: `(total) => '总共 ${total} 条'`

**列配置规范**
```tsx
const columns: ColumnsType<T> = [
  {
    title: '列名',
    dataIndex: 'fieldName',
    key: 'fieldName',
    // align 会自动设置为 center
    // ellipsis 会自动设置为 true
    width: 120, // 可选
    render: (text, record) => {
      // 自定义渲染
    }
  }
];
```

**操作列规范**
```tsx
{
  title: '操作',
  key: 'action',
  width: 200,
  render: (_, record) => (
    <Space size="middle">
      <a onClick={() => handleEdit(record)}>编辑</a>
      <a onClick={() => handleView(record)}>查看</a>
      <Popconfirm title="确定删除吗?" onConfirm={() => handleDelete(record)}>
        <a className="text-red-500">删除</a>
      </Popconfirm>
    </Space>
  )
}
```

### Form (表单)

**基础配置**
```tsx
<Form
  form={form}
  labelCol={{ span: 4 }}
  wrapperCol={{ span: 20 }}
  autoComplete="off"
  onFinish={onFinish}
  onFinishFailed={onFinishFailed}
>
  {/* 表单项 */}
</Form>
```

**表单项规范**

**文本输入**
```tsx
<Form.Item
  label="项目名称"
  name="projectName"
  rules={[{ required: true, message: '请输入项目名称!' }]}
>
  <Input
    placeholder="请输入项目名称"
    allowClear
    maxLength={100}
    showCount
  />
</Form.Item>
```

**多行文本**
```tsx
<Form.Item
  label="应用描述"
  name="description"
  rules={[{ required: true, message: '请输入应用描述' }]}
>
  <Input.TextArea
    placeholder="请输入应用描述"
    allowClear
    maxLength={500}
    showCount
    rows={4}
  />
</Form.Item>
```

**下拉选择**
```tsx
<Form.Item
  label="模型选择"
  name="modelId"
  rules={[{ required: true, message: '请选择模型' }]}
>
  <Select
    placeholder="请选择模型"
    allowClear
    options={modelOptions}
  />
</Form.Item>
```

**滑块输入**
```tsx
<Form.Item
  label="相似度阈值"
  name="similarityThreshold"
>
  <SliderInput min={0} max={1} step={0.1} />
</Form.Item>
```

**提交按钮组**
```tsx
<Form.Item label={null}>
  <div className="flex items-center justify-center gap-4">
    <Button type="primary" htmlType="submit" loading={loading}>
      提交
    </Button>
    <Button onClick={handleCancel}>
      取消
    </Button>
  </div>
</Form.Item>
```

**提示信息**
```tsx
<Form.Item label={null}>
  <div>tips: 知识库负责人审批通过后，可通过接入点使用知识库</div>
</Form.Item>
```

### Modal (弹窗)

**基础用法**
```tsx
<Modal
  title="创建应用"
  open={visible}
  onCancel={handleCancel}
  footer={null}
  width={600}
>
  <Form>
    {/* 表单内容 */}
  </Form>
</Modal>
```

**样式规范**
- 默认宽度: `600px`
- 标题: 使用默认样式
- Footer: 通常设置为`null`，在Form内自定义按钮组
- 关闭按钮: 保留默认右上角X按钮

### Button (按钮)

**按钮类型**
```tsx
// 主要按钮
<Button type="primary">主要操作</Button>

// 默认按钮
<Button>次要操作</Button>

// 危险按钮
<Button type="primary" danger>删除</Button>

// 文本按钮
<Button type="link">链接操作</Button>
```

**按钮尺寸**
```tsx
<Button size="large">大按钮</Button>    // 大按钮（重要操作）
<Button size="middle">中按钮</Button>   // 默认
<Button size="small">小按钮</Button>    // 表格内操作
```

**按钮状态**
```tsx
<Button loading={loading}>加载中</Button>
<Button disabled>禁用</Button>
<Button icon={<PlusOutlined />}>带图标</Button>
```

**按钮宽度**
```tsx
// 固定宽度（表单提交按钮）
<Button className="w-[160px]" type="primary">提交</Button>

// 大型操作按钮
<Button className="w-[220px]" size="large" type="primary">
  创建任务
</Button>
```

### Tag (标签)

**状态标签**
```tsx
<Tag color="success">已通过</Tag>
<Tag color="processing">进行中</Tag>
<Tag color="error">已拒绝</Tag>
<Tag color="warning">待审批</Tag>
<Tag color="default">已关闭</Tag>
```

**自定义样式标签**
```tsx
// 警告标签
<span className="inline-block rounded-[3px] text-[12px]/[22px] px-[6px] text-[#C0811D] bg-[#FED17D]">
  待处理
</span>

// 信息标签
<div className="flex items-center p-[6px] bg-[#E6E9FD] rounded-[5px] text-[#4F4FF6]">
  <Icon />
  <span>已选中</span>
</div>

// 角标
<div className="absolute right-0 top-0 h-[24px] px-[10px] bg-[#F35859] text-[#fff] text-[12px] rounded-bl-lg">
  HOT
</div>
```

### Banner (页面横幅)

**结构**
```tsx
<div className="flex w-full h-[120px] justify-between">
  {/* 主横幅 */}
  <div className="w-[74%] h-[120px] relative">
    <img className="w-full h-full object-cover rounded-[8px]" src={bannerBg} />
    <div className="w-full h-full absolute top-0 left-0 px-[32px] py-[24px]">
      <div className="text-[#333] text-[20px] font-bold mb-[15px]">
        {title}
      </div>
      <div className="text-[#545E74] text-[16px]">
        {description}
      </div>
    </div>
  </div>
  
  {/* 辅助横幅（教程入口） */}
  <a className="w-[24%] h-[120px] relative block" href={helperLink} target="_blank">
    <img className="w-full h-full object-cover rounded-[8px]" src={helperBg} />
    <div className="w-full h-full absolute top-0 left-0 px-[32px] py-[24px]">
      <div className="text-[#333] text-[20px] font-bold">教程</div>
      <div className="text-[#333] text-[14px]">{helperText}</div>
    </div>
  </a>
</div>
```

**样式规范**
- 高度: `120px`
- 圆角: `8px`
- 主横幅宽度: `74%`
- 辅助横幅宽度: `24%`
- 内边距: `px-[32px] py-[24px]`
- 标题字体: `text-[20px] font-bold`
- 描述字体: `text-[16px]`

### Card & Section (卡片与区块)

**内容卡片**
```tsx
<div className="bg-white rounded-[8px] p-6 shadow-sm">
  <div className="text-[16px] font-bold mb-4">卡片标题</div>
  <div>{content}</div>
</div>
```

**信息展示块**
```tsx
<div className="leading-8 bg-[#F5F7FF] p-4 rounded">
  <div className="text-[14px] text-[#333]">
    <strong>标签：</strong>{value}
  </div>
</div>
```

**可滚动内容块**
```tsx
<div className="bg-[#F5F7FF] max-h-[250px] overflow-y-auto rounded-lg p-4 border-[#8eb0f9] border-[1px]">
  {content}
</div>
```

---

## 交互模式

### 加载状态

**全局加载**
```tsx
import { getSpinIndicator } from '@/constants/spin';

<Spin indicator={getSpinIndicator()} spinning={loading}>
  {content}
</Spin>
```

**表格加载**
```tsx
import { getSpinPros } from '@/constants/spin';

<Table loading={getSpinPros(loading)} {...props} />
```

**按钮加载**
```tsx
<Button loading={submitting} type="primary">
  提交中
</Button>
```

### 确认操作

**删除确认**
```tsx
<Popconfirm
  title="确定删除吗?"
  description="删除后无法恢复"
  onConfirm={handleDelete}
  okText="确定"
  cancelText="取消"
>
  <a className="text-red-500">删除</a>
</Popconfirm>
```

**重要操作确认**
```tsx
Modal.confirm({
  title: '确认操作',
  content: '此操作将影响所有用户，是否继续？',
  okText: '确定',
  cancelText: '取消',
  onOk: handleConfirm,
});
```

### 消息提示

**成功提示**
```tsx
message.success('操作成功');
```

**错误提示**
```tsx
message.error('操作失败，请重试');
```

**警告提示**
```tsx
message.warning('请先完成必填项');
```

**信息提示**
```tsx
message.info('数据已同步');
```

### 表单验证

**基础验证**
```tsx
rules={[
  { required: true, message: '请输入项目名称' },
  { max: 100, message: '最多100个字符' },
  { pattern: /^[a-zA-Z0-9_]+$/, message: '只能包含字母、数字和下划线' }
]}
```

**自定义验证**
```tsx
rules={[
  {
    validator: async (_, value) => {
      if (!value || value.length < 6) {
        return Promise.reject(new Error('密码至少6位'));
      }
      return Promise.resolve();
    }
  }
]}
```

**动态验证**
```tsx
const handleValuesChange = (changedValues) => {
  if ('rerankId' in changedValues && changedValues.rerankId) {
    form.setFieldsValue({ topK: 1024 });
  }
};

<Form onValuesChange={handleValuesChange}>
  {/* ... */}
</Form>
```

### 列表操作

**批量操作**
```tsx
const [selectedRowKeys, setSelectedRowKeys] = useState([]);

const rowSelection = {
  selectedRowKeys,
  onChange: (keys) => setSelectedRowKeys(keys),
};

<BaseTable rowSelection={rowSelection} {...props} />

{selectedRowKeys.length > 0 && (
  <div className="mb-4">
    <span>已选择 {selectedRowKeys.length} 项</span>
    <Button onClick={handleBatchDelete}>批量删除</Button>
  </div>
)}
```

**行内操作**
```tsx
{
  title: '操作',
  key: 'action',
  render: (_, record) => (
    <Space size="middle">
      <a onClick={() => handleEdit(record)}>编辑</a>
      <a onClick={() => handleView(record)}>查看</a>
      <Dropdown
        menu={{
          items: [
            { key: 'copy', label: '复制' },
            { key: 'export', label: '导出' },
            { key: 'delete', label: '删除', danger: true },
          ],
          onClick: ({ key }) => handleMenuClick(key, record)
        }}
      >
        <a>更多</a>
      </Dropdown>
    </Space>
  )
}
```

### 页面跳转

**React Router跳转**
```tsx
import { useNavigate } from 'react-router';

const navigate = useNavigate();

// 普通跳转
navigate('/model/detail', { state: { id: modelId } });

// 替换当前历史
navigate('/no-auth', { replace: true });

// 返回上一页
navigate(-1);
```

**外部链接**
```tsx
<a href="https://docs.example.com" target="_blank" rel="noopener noreferrer">
  查看文档
</a>
```

### 刷新与同步

**页面刷新**
```tsx
// 数据刷新
const refresh = () => {
  fetchData();
};

// 整页刷新
window.location.reload();
```

**跨Tab同步**
```tsx
import { sendMessage } from '@/utils/channel';

// 切换工作空间后通知其他Tab
sendMessage({ type: 'WORKSPACE_CHANGED', data: newWorkspace });
window.location.reload();
```

---

## 响应式设计

### 最小宽度约束

**页面容器**
```css
min-w-[1260px]  /* 防止内容过度压缩 */
```

**表格横向滚动**
```tsx
<BaseTable
  xScroll="max-content"  // 内容宽度自适应
  // 或
  scroll={{ x: 1200 }}    // 固定宽度
  {...props}
/>
```

### 弹性布局

**Header布局**
```tsx
<header className="flex flex-row items-center justify-between">
  <div>{leftContent}</div>
  <div className="flex-1 flex items-center justify-end">
    {rightContent}
  </div>
</header>
```

**内容区布局**
```tsx
<div className="flex">
  <div className="w-[180px] shrink-0">{sidebar}</div>
  <div className="flex-1">{content}</div>
</div>
```

### 文本省略

**单行省略**
```css
.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

**多行省略**
```css
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

**表格列省略**
```tsx
// BaseTable 自动为所有列启用 ellipsis
// 如需禁用特定列
{
  title: '列名',
  dataIndex: 'field',
  ellipsis: false
}
```

---

## 可访问性

### 语义化标签

**导航**
```tsx
<nav className="bg-white h-full">
  <NavLink to="/">首页</NavLink>
</nav>
```

**主要内容**
```tsx
<main className="content-area">
  <Outlet />
</main>
```

**页眉页脚**
```tsx
<header className="site-header">...</header>
<footer className="site-footer">...</footer>
```

### 键盘导航

**可聚焦元素**
- 所有链接使用 `<a>` 或 `<NavLink>`
- 所有按钮使用 `<Button>`
- 表单元素使用Ant Design组件

**Tab顺序**
- 保持逻辑顺序：从上到下、从左到右
- 避免使用 `tabIndex > 0`

### ARIA属性

**标签关联**
```tsx
<Form.Item label="用户名" name="username">
  <Input aria-label="用户名" />
</Form.Item>
```

**状态提示**
```tsx
<Button loading aria-busy="true">
  加载中
</Button>
```

**工具提示**
```tsx
<Tooltip title="这是帮助信息" placement="top">
  <Icon />
</Tooltip>
```

### 颜色对比

**文字对比度**
- 确保文字与背景对比度 ≥ 4.5:1
- 大字号（18px+）对比度 ≥ 3:1

**状态区分**
- 不仅依赖颜色区分状态
- 配合图标、文字、边框等多种方式

---

## 最佳实践

### 1. 组件使用

✅ **推荐做法**
```tsx
// 使用 BaseTable 统一表格样式
import BaseTable from '@/components/BaseTable';

<BaseTable
  columns={columns}
  dataSource={data}
  loading={loading}
/>
```

❌ **不推荐做法**
```tsx
// 直接使用 Ant Design Table
import { Table } from 'antd';

<Table columns={columns} dataSource={data} />
```

### 2. 样式管理

✅ **推荐做法**
```tsx
// 使用 TailwindCSS 类名
<div className="flex items-center justify-between px-4 py-2">
  {content}
</div>

// 使用预定义颜色
<div className="text-[#333333] bg-[#F1F3FA]">
  {content}
</div>
```

❌ **不推荐做法**
```tsx
// 内联样式
<div style={{ display: 'flex', padding: '8px 16px' }}>
  {content}
</div>

// 随意定义颜色
<div style={{ color: '#123456', backgroundColor: '#abcdef' }}>
  {content}
</div>
```

### 3. 表单处理

✅ **推荐做法**
```tsx
const [form] = Form.useForm();

const handleSubmit = async (values) => {
  setLoading(true);
  try {
    await request('/api/submit', { body: values });
    message.success('提交成功');
    form.resetFields();
    onSuccess();
  } catch (error) {
    message.error('提交失败');
  } finally {
    setLoading(false);
  }
};

<Form form={form} onFinish={handleSubmit}>
  {/* 表单项 */}
  <Form.Item>
    <Button loading={loading} type="primary" htmlType="submit">
      提交
    </Button>
  </Form.Item>
</Form>
```

❌ **不推荐做法**
```tsx
// 手动管理表单状态
const [name, setName] = useState('');
const [email, setEmail] = useState('');

const handleSubmit = () => {
  // 手动验证
  if (!name) {
    alert('请输入姓名');
    return;
  }
  // ...
};
```

### 4. 加载状态

✅ **推荐做法**
```tsx
import { getSpinIndicator, getSpinPros } from '@/constants/spin';

// 全局加载
<Spin indicator={getSpinIndicator()} spinning={loading}>
  {content}
</Spin>

// 表格加载
<BaseTable loading={loading} {...props} />

// 按钮加载
<Button loading={submitting}>提交</Button>
```

❌ **不推荐做法**
```tsx
// 使用默认Spin
<Spin spinning={loading}>{content}</Spin>

// 手动显示加载文字
{loading ? <div>加载中...</div> : content}
```

### 5. 错误处理

✅ **推荐做法**
```tsx
try {
  const result = await request('/api/data');
  setData(result);
} catch (error) {
  console.error('Failed to fetch data:', error);
  message.error('获取数据失败，请重试');
}
```

❌ **不推荐做法**
```tsx
// 忽略错误
const result = await request('/api/data');
setData(result);

// 不友好的错误提示
.catch(err => alert('Error: ' + err.message));
```

### 6. 权限控制

✅ **推荐做法**
```tsx
import { use } from 'react';
import { CommonContext } from '@/context';

const Component = () => {
  const { routerList, user } = use(CommonContext);
  
  const hasPermission = routerList.includes('/admin/users');
  
  if (!hasPermission) {
    return <Navigate to="/no-auth" />;
  }
  
  return <div>{content}</div>;
};
```

❌ **不推荐做法**
```tsx
// 直接判断用户角色
if (user.role !== 'admin') {
  return null;
}
```

### 7. 路由设置

✅ **推荐做法**
```tsx
// 在路由配置中设置 handle
{
  path: 'model/detail',
  Component: ModelDetail,
  handle: {
    title: '模型详情'
  }
}

// 在组件中使用 useTitle
import { useTitle } from '@/hooks/useTitle';

const Component = () => {
  const title = useTitle();
  
  useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);
  
  return <div>{content}</div>;
};
```

❌ **不推荐做法**
```tsx
// 在组件中硬编码标题
useEffect(() => {
  document.title = '模型详情';
}, []);
```

### 8. 图标使用

✅ **推荐做法**
```tsx
import { Icon } from '@iconify/react';

// 使用私有化图标库
<Icon icon="zkh:ai-dev:xiaoxi" className="text-[16px]" />

// 使用 Ant Design 图标
import { PlusOutlined } from '@ant-design/icons';
<Button icon={<PlusOutlined />}>新增</Button>
```

❌ **不推荐做法**
```tsx
// 使用图片代替图标
<img src="/icons/message.png" alt="消息" />

// 使用未授权的图标库
<i className="fa fa-home"></i>
```

### 9. 性能优化

✅ **推荐做法**
```tsx
// 使用 useMemo 缓存计算结果
const menuList = useMemo(() => {
  return contextValue.menuList.filter(item => 
    item.children && item.children.length > 0
  );
}, [contextValue.menuList]);

// 使用 React.lazy 懒加载路由
const ModelDetail = lazy(() => import('@/views/Model/Detail'));

// 列表使用 key
{items.map(item => (
  <Item key={item.id} data={item} />
))}
```

❌ **不推荐做法**
```tsx
// 每次渲染都计算
const menuList = contextValue.menuList.filter(...);

// 使用索引作为 key
{items.map((item, index) => (
  <Item key={index} data={item} />
))}
```

### 10. TypeScript类型

✅ **推荐做法**
```tsx
import type { FormProps } from 'antd';
import type { ColumnType } from 'antd/es/table';

interface DataType {
  id: number;
  name: string;
  status: 'active' | 'inactive';
}

const columns: ColumnType<DataType>[] = [...];

const onFinish: FormProps<DataType>['onFinish'] = (values) => {
  // values 自动推断类型
};
```

❌ **不推荐做法**
```tsx
// 使用 any
const columns: any[] = [...];

const onFinish = (values: any) => {
  // 失去类型检查
};
```

---

## 常见场景示例

### 列表页

```tsx
const ListPage = () => {
  const [data, setData] = useState<DataType[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await request('/api/list', {
        method: 'POST',
        body: { page, pageSize }
      });
      setData(result.list);
      setTotal(result.total);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, pageSize]);

  const columns: ColumnType<DataType>[] = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <a onClick={() => handleEdit(record)}>编辑</a>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(record)}>
            <a className="text-red-500">删除</a>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div className="mb-4 flex justify-between">
        <div className="text-[20px] font-bold">数据列表</div>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建
        </Button>
      </div>
      
      <BaseTable
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{
          current: page,
          pageSize,
          total,
          onChange: (newPage, newPageSize) => {
            setPage(newPage);
            setPageSize(newPageSize);
          }
        }}
      />
    </div>
  );
};
```

### 详情页

```tsx
const DetailPage = () => {
  const { id } = useParams();
  const [data, setData] = useState<DetailType>();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const result = await request(`/api/detail/${id}`);
        setData(result);
      } catch (error) {
        message.error('获取详情失败');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDetail();
  }, [id]);

  if (loading) {
    return <Spin spinning={loading} />;
  }

  return (
    <div className="max-w-[1188px] mx-auto">
      <div className="text-[24px] font-bold mb-6">{data?.name}</div>
      
      <div className="bg-white rounded-[8px] p-6 mb-4">
        <div className="text-[16px] font-bold mb-4">基本信息</div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-[#9297A9]">创建时间：</span>
            <span>{data?.createTime}</span>
          </div>
          <div>
            <span className="text-[#9297A9]">更新时间：</span>
            <span>{data?.updateTime}</span>
          </div>
        </div>
      </div>
      
      <div className="bg-[#F5F7FF] rounded-lg p-4">
        <div className="text-[14px] text-[#333]">
          <strong>描述：</strong>{data?.description}
        </div>
      </div>
    </div>
  );
};
```

### 表单页

```tsx
const FormPage = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values: FormType) => {
    setLoading(true);
    try {
      await request('/api/create', {
        method: 'POST',
        body: values
      });
      message.success('创建成功');
      navigate(-1);
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[800px] mx-auto">
      <div className="text-[20px] font-bold mb-6">创建项目</div>
      
      <Form
        form={form}
        labelCol={{ span: 4 }}
        wrapperCol={{ span: 20 }}
        onFinish={handleSubmit}
      >
        <Form.Item
          label="项目名称"
          name="name"
          rules={[{ required: true, message: '请输入项目名称' }]}
        >
          <Input placeholder="请输入项目名称" maxLength={100} showCount />
        </Form.Item>

        <Form.Item
          label="项目描述"
          name="description"
          rules={[{ required: true, message: '请输入项目描述' }]}
        >
          <Input.TextArea
            placeholder="请输入项目描述"
            maxLength={500}
            showCount
            rows={4}
          />
        </Form.Item>

        <Form.Item label={null}>
          <div className="flex items-center justify-center gap-4">
            <Button type="primary" htmlType="submit" loading={loading}>
              创建
            </Button>
            <Button onClick={() => navigate(-1)}>
              取消
            </Button>
          </div>
        </Form.Item>
      </Form>
    </div>
  );
};
```

---

## 资源与工具

### 设计资源
- [Ant Design 官方文档](https://ant.design/)
- [TailwindCSS 文档](https://tailwindcss.com/)
- [Iconify 图标库](https://iconify.design/)

### 开发工具
- **Chrome DevTools**: 调试响应式布局
- **React DevTools**: 组件性能分析
- **Lighthouse**: 可访问性检测

### 代码规范
- 使用 ESLint + Prettier 保持代码风格统一
- 遵循 React Hooks 最佳实践
- 使用 TypeScript 严格模式

---

## 更新日志

### v1.0.0 (2026-01-27)
- 初始版本
- 基于现有平台提炼UI/UX设计规范
- 包含完整的组件规范和最佳实践

---

## 自定义组件

本 skill 包含以下自定义组件，完整源码位于 `components/` 和 `hooks/` 目录。

### 📦 组件清单

| 组件 | 文件 | 说明 |
|------|------|------|
| **BaseTable** | [components/BaseTable.tsx](./components/BaseTable.tsx) | 统一表格组件，封装 Ant Design Table |
| **Tag** | [components/Tag.tsx](./components/Tag.tsx) | 自定义标签组件 |
| **SliderInput** | [components/SliderInput.tsx](./components/SliderInput.tsx) | 滑块与数字输入组合 |
| **spin** | [components/spin.tsx](./components/spin.tsx) | 统一加载动画配置 |
| **Banner** | [components/Banner.tsx](./components/Banner.tsx) | 页面横幅组件 |
| **BannerConstants** | [components/BannerConstants.ts](./components/BannerConstants.ts) | 横幅配置 |
| **useTitle** | [hooks/useTitle.ts](./hooks/useTitle.ts) | 页面标题管理 Hook |

### 🔗 依赖关系

```mermaid
graph TB
    subgraph "核心组件"
        BaseTable[BaseTable.tsx]
        Tag[Tag.tsx]
        SliderInput[SliderInput.tsx]
        Banner[Banner.tsx]
    end
    
    subgraph "工具与配置"
        Spin[spin.tsx]
        UseTitle[useTitle.ts]
        BannerConst[BannerConstants.ts]
    end
    
    subgraph "外部依赖"
        AntD[Ant Design]
        Iconify[@iconify/react]
        Router[react-router]
    end
    
    BaseTable --> Spin
    BaseTable --> AntD
    
    SliderInput --> AntD
    
    Spin --> Iconify
    
    Banner --> BannerConst
    
    UseTitle --> Router
    
    style BaseTable fill:#E6E9FD
    style Tag fill:#E6E9FD
    style SliderInput fill:#E6E9FD
    style Banner fill:#E6E9FD
```

### 📋 组件快速参考

#### BaseTable 使用示例
```tsx
import BaseTable from '@/components/BaseTable';

<BaseTable
  columns={columns}
  dataSource={data}
  loading={loading}
  pagination={{ current: page, pageSize, total }}
  rowKey="id"
/>
```

#### Tag 使用示例
```tsx
import Tag from '@/components/Tag';

<Tag name="机器学习" id={1} />
```

#### SliderInput 使用示例
```tsx
import SliderInput from '@/components/SliderInput';

<Form.Item label="相似度阈值" name="threshold">
  <SliderInput min={0} max={1} step={0.01} />
</Form.Item>
```

#### Banner 使用示例
```tsx
import Banner from '@/components/Banner';

<Banner type="model" />
```

#### useTitle 使用示例
```tsx
import { useTitle } from '@/hooks/useTitle';

const Component = () => {
  const title = useTitle();
  
  useEffect(() => {
    if (title) {
      document.title = title;
    }
  }, [title]);
  
  return <div>{content}</div>;
};
```

#### Layout 使用示例
```tsx
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

// 完整布局
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

// 简化布局
<Layout
  mode="simple"
  headerProps={{ 
    user: { username: 'user@example.com' },
    isLogin: true 
  }}
>
  {/* 页面内容 */}
</Layout>
```

#### Nav 使用示例
```tsx
import Nav from '@/components/Nav';

const menuList = [
  {
    name: '开发',
    children: [
      { name: '模型', icon: 'icon-moxing', link: '/model' },
      { name: '应用', icon: 'icon-yingyong', link: '/application' },
    ]
  }
];

<Nav menuList={menuList} logoLink="/" />
```

#### Header 使用示例
```tsx
import Header from '@/components/Header';

const user = {
  username: 'user@example.com',
  nickname: '测试者',
  avatar: '/path/to/avatar.png'
};

// 常规模式
<Header
  mode="common"
  user={user}
  isLogin={true}
  headerMenu={[
    { icon: 'zkh:ai-dev:rili', link: 'https://docs.example.com', title: '文档' }
  ]}
/>

// 简化模式
<Header
  mode="simple"
  user={user}
  isLogin={true}
/>
```

### 🚀 快速开始

1. **复制文件到项目**
   ```bash
   # 复制所有组件
   cp -r skills/ui-ux/components/* src/components/
   cp -r skills/ui-ux/hooks/* src/hooks/
   cp -r skills/ui-ux/styles/* src/styles/
   cp -r skills/ui-ux/assets/* src/assets/
   cp -r skills/ui-ux/types/* src/types/
   ```

2. **引入全局样式**
   在项目入口文件（如 `main.tsx`）中引入：
   ```tsx
   import './styles/global.css';
   ```

3. **安装依赖**
   ```bash
   pnpm add antd @iconify/react react-router
   ```

4. **在项目中使用**
   按照上述示例导入并使用组件

### 📖 详细文档

每个组件的详细说明和完整源码，请查看对应的文件：
- [BaseTable.tsx](./components/BaseTable.tsx) - 完整 TypeScript 类型定义和注释
- [Tag.tsx](./components/Tag.tsx) - 简洁的标签组件
- [SliderInput.tsx](./components/SliderInput.tsx) - 参数调整组件
- [spin.tsx](./components/spin.tsx) - 加载动画配置
- [Banner.tsx](./components/Banner.tsx) - 横幅组件
- [Nav.tsx](./components/Nav.tsx) - 侧边导航组件
- [Header.tsx](./components/Header.tsx) - 头部导航组件
- [Layout.tsx](./components/Layout.tsx) - 布局组件
- [useTitle.ts](./hooks/useTitle.ts) - 标题管理 Hook

**样式和资源文件：**
- [global.css](./styles/global.css) - 全局样式文件
- [assets/](./assets/) - 图片资源目录
- [types/assets.d.ts](./types/assets.d.ts) - 图片资源类型声明

### 📚 组件管理

所有自定义组件与主 skill 文档分离管理：
- **SKILL.md**: 设计规范、使用指南、最佳实践
- **components/**: 可复用的组件源码（9个）
- **hooks/**: 可复用的 Hooks 源码（1个）
- **styles/**: 全局样式文件
- **assets/**: 图片资源目录
- **types/**: 类型声明文件
- **README.md**: 组件库说明文档

这种分离管理的优势：
- ✅ 组件代码独立维护
- ✅ 可以单独更新组件而不影响文档
- ✅ 便于将组件集成到其他项目
- ✅ 代码与文档职责清晰
- ✅ 包含完整的样式和资源文件

### 🔄 版本历史

**v2.0.0** (2026-01-27) - 重大升级
- ✨ 新增 Nav、Header、Layout 三个核心组件
- ✨ 新增 global.css 全局样式文件
- ✨ 新增 assets 图片资源目录
- ✨ 新增 assets.d.ts 类型声明
- 🐛 修复 Banner 组件图片引用路径
- 🐛 修复 Nav 激活状态样式问题
- ✨ BannerConstants 支持11种类型
- 📝 更新所有组件文档

**v1.0.0** (2026-01-27) - 初始版本
- ✨ 基础组件: BaseTable、Tag、SliderInput、spin、Banner
- ✨ 自定义 Hook: useTitle
- 📝 完整的设计规范文档

---

**维护者**: AI Developer Platform Team  
**最后更新**: 2026-01-27
