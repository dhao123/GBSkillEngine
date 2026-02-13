import { useState, useEffect } from 'react'
import { Tabs, Card, Button, message, Modal, Spin, Tag, Tooltip, Popconfirm } from 'antd'
import {
  PlusOutlined,
  ApiOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons'
import { settingsApi } from '../../services/api'
import LLMConfigForm from './LLMConfigForm'
import UsageMonitor from './UsageMonitor'

// 类型定义
interface LLMConfig {
  id: number
  provider: string
  name: string
  model_name: string
  endpoint?: string
  temperature: number
  max_tokens: number
  timeout: number
  api_key_masked: string
  has_api_secret: boolean
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

interface LLMConfigListResponse {
  total: number
  items: LLMConfig[]
}

interface LLMProviderInfo {
  provider: string
  name: string
  description: string
  models: string[]
  default_endpoint: string
  requires_secret: boolean
  supports_custom_endpoint: boolean
}

interface ProviderListResponse {
  providers: LLMProviderInfo[]
}

interface SystemInfo {
  version: string
  llm_mode: string
  default_llm_config_id: number | null
  default_llm_provider: string | null
  default_llm_model: string | null
}

// 供应商图标和颜色
const PROVIDER_STYLES: Record<string, { color: string; bgColor: string }> = {
  openai: { color: '#10a37f', bgColor: '#e6f7f1' },
  anthropic: { color: '#d97706', bgColor: '#fef3c7' },
  zkh: { color: '#7c3aed', bgColor: '#ede9fe' },
  local: { color: '#6b7280', bgColor: '#f3f4f6' },
}

const PROVIDER_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  zkh: '震坤行',
  local: '本地模型',
}

export default function Settings() {
  const [loading, setLoading] = useState(false)
  const [configs, setConfigs] = useState<LLMConfig[]>([])
  const [providers, setProviders] = useState<LLMProviderInfo[]>([])
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<LLMConfig | null>(null)
  const [testingId, setTestingId] = useState<number | null>(null)

  // 加载数据
  const loadData = async () => {
    setLoading(true)
    try {
      const [configRes, providerRes, sysRes] = await Promise.all([
        settingsApi.getLLMConfigs<LLMConfigListResponse>(),
        settingsApi.getProviders<ProviderListResponse>(),
        settingsApi.getSystemInfo<SystemInfo>(),
      ])
      setConfigs(configRes.items)
      setProviders(providerRes.providers)
      setSystemInfo(sysRes)
    } catch (error) {
      message.error('加载配置失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // 测试连接
  const handleTestConnection = async (id: number) => {
    setTestingId(id)
    try {
      const result = await settingsApi.testConnection<{
        success: boolean
        message: string
        latency_ms?: number
      }>(id)
      
      if (result.success) {
        message.success(`连接成功！延迟: ${result.latency_ms}ms`)
      } else {
        message.error(`连接失败: ${result.message}`)
      }
    } catch (error) {
      message.error('测试连接失败')
    } finally {
      setTestingId(null)
    }
  }

  // 设为默认
  const handleSetDefault = async (id: number) => {
    try {
      await settingsApi.setDefaultLLMConfig(id)
      message.success('已设为默认配置')
      loadData()
    } catch (error) {
      message.error('设置失败')
    }
  }

  // 删除配置
  const handleDelete = async (id: number) => {
    try {
      await settingsApi.deleteLLMConfig(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  // 打开编辑弹窗
  const openEditModal = (config: LLMConfig | null) => {
    setEditingConfig(config)
    setModalVisible(true)
  }

  // 关闭弹窗
  const handleModalClose = () => {
    setModalVisible(false)
    setEditingConfig(null)
  }

  // 保存配置
  const handleSave = async (values: Record<string, unknown>) => {
    try {
      if (editingConfig) {
        await settingsApi.updateLLMConfig(editingConfig.id, values)
        message.success('更新成功')
      } else {
        await settingsApi.createLLMConfig(values)
        message.success('创建成功')
      }
      handleModalClose()
      loadData()
    } catch (error) {
      message.error('保存失败')
    }
  }

  // 渲染配置卡片
  const renderConfigCard = (config: LLMConfig) => {
    const style = PROVIDER_STYLES[config.provider] || PROVIDER_STYLES.local
    const providerName = PROVIDER_NAMES[config.provider] || config.provider
    
    return (
      <Card
        key={config.id}
        className="mb-4"
        style={{ borderLeft: `4px solid ${style.color}` }}
        actions={[
          <Tooltip title="测试连接" key="test">
            <Button
              type="text"
              icon={<ApiOutlined />}
              loading={testingId === config.id}
              onClick={() => handleTestConnection(config.id)}
            >
              测试
            </Button>
          </Tooltip>,
          <Tooltip title="编辑" key="edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openEditModal(config)}
            >
              编辑
            </Button>
          </Tooltip>,
          config.is_default ? (
            <Tag color="gold" key="default" icon={<StarFilled />}>
              默认
            </Tag>
          ) : (
            <Tooltip title="设为默认" key="setDefault">
              <Button
                type="text"
                icon={<StarOutlined />}
                onClick={() => handleSetDefault(config.id)}
              >
                设为默认
              </Button>
            </Tooltip>
          ),
          <Popconfirm
            key="delete"
            title="确定删除此配置？"
            onConfirm={() => handleDelete(config.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>,
        ]}
      >
        <Card.Meta
          avatar={
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: 8,
                backgroundColor: style.bgColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 20,
                fontWeight: 'bold',
                color: style.color,
              }}
            >
              {providerName.charAt(0)}
            </div>
          }
          title={
            <div className="flex items-center gap-2">
              <span>{config.name}</span>
              {config.is_active ? (
                <Tag color="green" icon={<CheckCircleOutlined />}>
                  启用
                </Tag>
              ) : (
                <Tag color="default" icon={<ExclamationCircleOutlined />}>
                  禁用
                </Tag>
              )}
            </div>
          }
          description={
            <div className="text-gray-500">
              <div>供应商: {providerName}</div>
              <div>模型: {config.model_name}</div>
              <div>API Key: {config.api_key_masked}</div>
              {config.endpoint && <div>端点: {config.endpoint}</div>}
            </div>
          }
        />
      </Card>
    )
  }

  // LLM配置Tab内容
  const LLMConfigTab = () => (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div className="text-gray-500">
          配置LLM供应商以启用真实的Skill编译功能
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => openEditModal(null)}
        >
          添加配置
        </Button>
      </div>
      
      <Spin spinning={loading}>
        {configs.length === 0 ? (
          <Card className="text-center py-8">
            <div className="text-gray-400 mb-4">暂无LLM配置</div>
            <Button type="primary" onClick={() => openEditModal(null)}>
              添加第一个配置
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {configs.map(renderConfigCard)}
          </div>
        )}
      </Spin>
    </div>
  )

  // 系统信息Tab内容
  const SystemInfoTab = () => (
    <Card>
      <div className="space-y-4">
        <div className="flex justify-between border-b pb-2">
          <span className="text-gray-500">系统版本</span>
          <span>{systemInfo?.version || '-'}</span>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-gray-500">LLM模式</span>
          <Tag color={systemInfo?.llm_mode === 'real' ? 'green' : 'orange'}>
            {systemInfo?.llm_mode === 'real' ? '真实模式' : 'Mock模式'}
          </Tag>
        </div>
        <div className="flex justify-between border-b pb-2">
          <span className="text-gray-500">默认LLM供应商</span>
          <span>
            {systemInfo?.default_llm_provider
              ? PROVIDER_NAMES[systemInfo.default_llm_provider] || systemInfo.default_llm_provider
              : '未配置'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">默认模型</span>
          <span>{systemInfo?.default_llm_model || '未配置'}</span>
        </div>
      </div>
    </Card>
  )

  const tabItems = [
    {
      key: 'llm',
      label: 'LLM配置',
      children: <LLMConfigTab />,
    },
    {
      key: 'monitor',
      label: '监控数据',
      children: <UsageMonitor />,
    },
    {
      key: 'system',
      label: '系统信息',
      children: <SystemInfoTab />,
    },
  ]

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">系统配置</h1>
        <p className="text-gray-500 mt-1">管理LLM配置和系统设置</p>
      </div>
      
      <Card>
        <Tabs items={tabItems} />
      </Card>
      
      <Modal
        title={editingConfig ? '编辑LLM配置' : '添加LLM配置'}
        open={modalVisible}
        onCancel={handleModalClose}
        footer={null}
        width={600}
        destroyOnClose
      >
        <LLMConfigForm
          initialValues={editingConfig}
          providers={providers}
          onSubmit={handleSave}
          onCancel={handleModalClose}
        />
      </Modal>
    </div>
  )
}
