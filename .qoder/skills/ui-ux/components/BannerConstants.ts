/**
 * Banner 组件配置
 */

import ApplicationBg from '../assets/banner/application.png';
import McpBg from '../assets/banner/mcp.png';
import ModelBg from '../assets/banner/moxingguangchang.png';
import TestDatasetBg from '../assets/banner/pingceshujuji.png';
import EndpointBg from '../assets/banner/zaixiantuili.png';
import PluginsBg from '../assets/banner/chajianguangchang.png';
import ObserveBg from '../assets/banner/jieruguancedian.png';

export type BannerType = 
  | 'model' 
  | 'knowledge' 
  | 'application' 
  | 'testing' 
  | 'mcp'
  | 'endpoint'
  | 'plugins'
  | 'observe'
  | 'dataset'
  | 'dimension'
  | 'tasks';

interface BannerConfig {
  title: string;
  description: string;
  bannerBg: string;
  helperLink: string;
  helperText: string;
  needsHelper: boolean;
  openNewTab?: boolean;
}

/**
 * 页面横幅配置字典
 * 
 * 定义各个功能模块的横幅展示内容
 */
export const PageHeaderBannerConfig: Record<BannerType, BannerConfig> = {
  application: {
    title: '应用广场',
    description: '提供已发布的AI产品、智能体、工作流等AI应用，快速构建大模型应用',
    bannerBg: ApplicationBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何开发智能体',
    needsHelper: true,
    openNewTab: true,
  },
  dataset: {
    title: '评测集',
    description: '依据评测需求增加评测集，支持多版本，应用于应用评测任务',
    bannerBg: TestDatasetBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何创建合适的评测集',
    needsHelper: true,
    openNewTab: true,
  },
  dimension: {
    title: '评测维度',
    description: '依据评测需求增加维度模板，支持自定义多级维度、多级分数，应用于应用评测任务',
    bannerBg: PluginsBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何创建合适的维度',
    needsHelper: true,
    openNewTab: true,
  },
  endpoint: {
    title: '在线推理',
    description: '提供实时的模型推理服务，通过推理接入点灵活调整资源并访问模型，可通过监控查看运行状况',
    bannerBg: EndpointBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何使用模型推理接入点',
    needsHelper: true,
    openNewTab: true,
  },
  knowledge: {
    title: '知识库',
    description: '构建企业专属知识库，提供智能检索能力',
    bannerBg: TestDatasetBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何创建知识库',
    needsHelper: true,
    openNewTab: true,
  },
  mcp: {
    title: 'MCP广场',
    description: '提供已发布的MCP服务，链接智能，即点即用',
    bannerBg: McpBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '什么是MCP服务',
    needsHelper: true,
    openNewTab: true,
  },
  model: {
    title: '模型广场',
    description: '提供多种模型选型，包含通义模型、OpenAI模型、DeepSeek模型、ZKH行业大模型等，可根据业务需求选择',
    bannerBg: ModelBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何选择合适的模型',
    needsHelper: true,
    openNewTab: true,
  },
  observe: {
    title: '接入点观测',
    description: '基于SLS日志服务提供接入点指标监控，实时数据展示',
    bannerBg: ObserveBg,
    helperLink: '',
    helperText: '',
    needsHelper: false,
    openNewTab: false,
  },
  plugins: {
    title: '插件广场',
    description: '公共插件广场，根据业务需求选择特定插件，将震坤行业务能力、三方服务能力、业务知识与大模型进行组合串联，灵活搭建AI应用',
    bannerBg: PluginsBg,
    helperLink: '',
    helperText: '如何申请使用和配置插件',
    needsHelper: true,
    openNewTab: false,
  },
  tasks: {
    title: '应用评测',
    description: '通过选择评测集，批量评测应用效果，支持自定义评测维度，评测过程信息透明化，全方位评测应用效果',
    bannerBg: ApplicationBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '如何创建合适的评测任务',
    needsHelper: true,
    openNewTab: true,
  },
  testing: {
    title: '评测中心',
    description: '全方位评测AI模型和应用性能',
    bannerBg: TestDatasetBg,
    helperLink: 'https://aidev-docs.zkh360.com',
    helperText: '查看评测指南',
    needsHelper: true,
    openNewTab: true,
  },
};
