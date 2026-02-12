/**
 * 默认菜单配置
 * 定义平台的导航菜单结构
 * 
 * @usage
 * 在 CommonContext 中使用默认菜单，或根据后端返回的菜单数据动态渲染
 */
import type { Menu } from '../types/common';

export const defaultMenus: Menu[] = [
  {
    children: [
      {
        children: [],
        icon: 'icon-yingyongkaifa',
        link: '/application/dashboard',
        name: '应用广场',
        type: 'MENU',
      },
      {
        children: [],
        icon: 'icon-moxingguance',
        link: '/application/management',
        name: '应用管理',
        type: 'MENU',
      },
      {
        children: [],
        icon: '',
        link: '/application/:id',
        name: '应用详情页',
        type: 'MENU',
      },
      {
        children: [],
        icon: '',
        link: '/application/config/:id',
        name: '应用配置',
        type: 'MENU',
      },
    ],
    name: '应用中心',
    type: 'MENU',
  },
  {
    children: [
      {
        children: [],
        icon: 'icon-yingyongkaifa',
        link: '/mcp/dashboard',
        name: 'MCP广场',
        type: 'MENU',
      },
      {
        children: [],
        icon: 'icon-moxingguance',
        link: '/mcp/management',
        name: 'MCP管理',
        type: 'MENU',
      },
      {
        children: [],
        icon: '',
        link: '/mcp/:id',
        name: 'MCP详情页',
        type: 'MENU',
      },
      {
        children: [],
        icon: '',
        link: '/mcp/config/:id',
        name: 'MCP配置',
        type: 'MENU',
      },
    ],
    name: 'MCP',
    type: 'MENU',
  },
  {
    children: [
      {
        children: [],
        coding: '',
        icon: 'icon-moxingpingce',
        link: '/testing/dimension',
        name: '评测维度',
        type: 'MENU',
      },
      {
        children: [],
        coding: '',
        icon: 'icon-jueceyinqing',
        link: '/testing/dataset',
        name: '评测数据集',
        type: 'MENU',
      },
      {
        children: [
          {
            children: [],
            coding: '',
            icon: '',
            link: '/testing/task/:id',
            name: '评测历史',
            type: 'MENU',
          },
          {
            children: [],
            coding: '',
            icon: '',
            link: '/testing/task/:id/:subid/subtask',
            name: '评测历史明细',
            type: 'MENU',
          },
          {
            children: [],
            coding: '',
            icon: '',
            link: '/testing/task/:id/:subid/result',
            name: '评测任务结果',
            type: 'MENU',
          },
          {
            children: [],
            coding: '',
            icon: '',
            link: '/testing/task/:id/:subid/subtask/annotation',
            name: '评测题目标注',
            type: 'MENU',
          },
          {
            children: [],
            coding: '',
            icon: '',
            link: '/testing/task/config',
            name: '配置评测任务',
            type: 'MENU',
          },
        ],
        coding: '',
        icon: 'material-symbols-light:inbox-text-asterisk-rounded',
        link: '/testing/task',
        name: '评测任务',
        type: 'MENU',
      },
    ],
    coding: '',
    icon: '',
    link: '',
    name: '评测中心',
    type: 'MENU',
  },
  {
    children: [
      {
        children: [],
        coding: '',
        icon: 'icon-a-moxingguangchang2x',
        link: '/model/dashboard',
        name: '模型广场',
        type: 'MENU',
      },
      {
        children: [],
        coding: '',
        icon: 'icon-wodemoxing',
        link: '/model/my',
        name: '我的模型',
        type: 'MENU',
      },
      {
        children: [],
        coding: '',
        icon: 'icon-moxingtuili',
        link: '/model/endpoint',
        name: '在线推理',
        type: 'MENU',
      },
      {
        children: [],
        coding: '',
        icon: '',
        link: '/model/:id',
        name: '模型详情页',
        type: 'MENU',
      },
      {
        children: [],
        coding: '',
        icon: 'icon-moxingguanli',
        link: '/model/observe',
        name: '模型观测',
        type: 'MENU',
      },
    ],
    coding: '',
    icon: '',
    link: '',
    name: '模型中心',
    type: 'MENU',
  },
  {
    children: [
      {
        children: [],
        icon: 'icon-shujuji',
        link: '/knowledge',
        name: '知识库管理',
        type: 'MENU',
      },
      {
        children: [],
        link: '/knowledge/:id/edit',
        name: '编辑知识库',
        type: 'MENU',
      },
      {
        children: [],
        link: '/knowledge/create',
        name: '创建知识库',
        type: 'MENU',
      },
      {
        children: [],
        link: '/knowledge/:id',
        name: '知识库详情页',
        type: 'MENU',
      },
      {
        children: [],
        link: '/knowledge/doc/:id/chunk',
        name: '知识库切片',
        type: 'MENU',
      },
    ],
    coding: '',
    icon: '',
    link: '',
    name: '数据中心',
    type: 'MENU',
  },
  {
    children: [
      {
        children: [],
        icon: 'icon-shujubiaozhu',
        link: '/system/api-key',
        name: 'APIKey管理',
        type: 'MENU',
      },
      {
        children: [],
        icon: 'icon-gerenzhongxin',
        link: '/system/member',
        name: '成员管理',
        type: 'MENU',
      },
    ],
    icon: '',
    link: '',
    name: '系统管理',
    type: 'MENU',
  },
] as const;
