import { useState, useEffect } from 'react'
import {
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Button,
  Space,
  Collapse,
  Radio,
} from 'antd'

interface LLMProviderInfo {
  provider: string
  name: string
  description: string
  models: string[]
  default_endpoint: string
  requires_secret: boolean
  supports_custom_endpoint: boolean
}

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
}

interface LLMConfigFormProps {
  initialValues: LLMConfig | null
  providers: LLMProviderInfo[]
  onSubmit: (values: Record<string, unknown>) => Promise<void>
  onCancel: () => void
}

// 供应商显示配置
const PROVIDER_DISPLAY: Record<string, { name: string; icon: string }> = {
  openai: { name: 'OpenAI', icon: 'O' },
  anthropic: { name: 'Anthropic', icon: 'A' },
  baidu: { name: '百度文心', icon: 'B' },
  aliyun: { name: '阿里通义', icon: 'Q' },
  zkh: { name: '震坤行', icon: 'Z' },
  local: { name: '本地模型', icon: 'L' },
}

export default function LLMConfigForm({
  initialValues,
  providers,
  onSubmit,
  onCancel,
}: LLMConfigFormProps) {
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<string>(
    initialValues?.provider || 'openai'
  )

  // 获取当前供应商信息
  const currentProvider = providers.find((p) => p.provider === selectedProvider)

  // 监听provider变化
  useEffect(() => {
    if (currentProvider) {
      // 设置默认模型
      if (!initialValues) {
        form.setFieldValue('model_name', currentProvider.models[0])
      }
      // 设置默认端点
      if (currentProvider.supports_custom_endpoint && !form.getFieldValue('endpoint')) {
        form.setFieldValue('endpoint', currentProvider.default_endpoint)
      }
    }
  }, [selectedProvider, currentProvider, form, initialValues])

  // 提交表单
  const handleSubmit = async (values: Record<string, unknown>) => {
    setSubmitting(true)
    try {
      await onSubmit(values)
    } finally {
      setSubmitting(false)
    }
  }

  // 供应商选项
  const providerOptions = providers.map((p) => ({
    value: p.provider,
    label: (
      <div className="flex items-center gap-2">
        <span
          className="w-6 h-6 rounded flex items-center justify-center text-xs font-bold"
          style={{
            backgroundColor:
              p.provider === 'openai'
                ? '#e6f7f1'
                : p.provider === 'anthropic'
                ? '#fef3c7'
                : p.provider === 'baidu'
                ? '#e8eafc'
                : p.provider === 'aliyun'
                ? '#fff2e8'
                : p.provider === 'zkh'
                ? '#ede9fe'
                : '#f3f4f6',
            color:
              p.provider === 'openai'
                ? '#10a37f'
                : p.provider === 'anthropic'
                ? '#d97706'
                : p.provider === 'baidu'
                ? '#2932e1'
                : p.provider === 'aliyun'
                ? '#ff6a00'
                : p.provider === 'zkh'
                ? '#7c3aed'
                : '#6b7280',
          }}
        >
          {PROVIDER_DISPLAY[p.provider]?.icon || p.provider.charAt(0).toUpperCase()}
        </span>
        <span>{PROVIDER_DISPLAY[p.provider]?.name || p.name}</span>
      </div>
    ),
  }))

  return (
    <Form
      form={form}
      layout="vertical"
      initialValues={{
        provider: initialValues?.provider || 'openai',
        name: initialValues?.name || '',
        model_name: initialValues?.model_name || '',
        endpoint: initialValues?.endpoint || '',
        temperature: initialValues?.temperature ?? 0.7,
        max_tokens: initialValues?.max_tokens ?? 4096,
        timeout: initialValues?.timeout ?? 60,
        is_default: initialValues?.is_default ?? false,
      }}
      onFinish={handleSubmit}
    >
      {/* 供应商选择 */}
      <Form.Item
        name="provider"
        label="LLM供应商"
        rules={[{ required: true, message: '请选择供应商' }]}
      >
        <Radio.Group
          optionType="button"
          buttonStyle="solid"
          onChange={(e) => setSelectedProvider(e.target.value)}
          disabled={!!initialValues}
        >
          {providers.map((p) => (
            <Radio.Button key={p.provider} value={p.provider}>
              {PROVIDER_DISPLAY[p.provider]?.name || p.name}
            </Radio.Button>
          ))}
        </Radio.Group>
      </Form.Item>

      {currentProvider && (
        <div className="text-gray-500 text-sm mb-4 -mt-2">
          {currentProvider.description}
        </div>
      )}

      {/* 配置名称 */}
      <Form.Item
        name="name"
        label="配置名称"
        rules={[{ required: true, message: '请输入配置名称' }]}
      >
        <Input placeholder="如：生产环境GPT-4" />
      </Form.Item>

      {/* 模型选择 */}
      <Form.Item
        name="model_name"
        label="模型"
        rules={[{ required: true, message: '请选择模型' }]}
      >
        <Select
          showSearch
          placeholder="选择模型"
          options={currentProvider?.models.map((m) => ({ value: m, label: m })) || []}
        />
      </Form.Item>

      {/* API Key */}
      <Form.Item
        name="api_key"
        label="API Key"
        rules={[
          {
            required: !initialValues,
            message: '请输入API Key',
          },
        ]}
        extra={initialValues ? '留空则不更新' : undefined}
      >
        <Input.Password
          placeholder={initialValues ? '输入新的API Key或留空' : '输入API Key'}
        />
      </Form.Item>

      {/* API Secret (部分供应商需要) */}
      {currentProvider?.requires_secret && (
        <Form.Item
          name="api_secret"
          label="API Secret"
          rules={[
            {
              required: !initialValues,
              message: '请输入API Secret',
            },
          ]}
          extra={initialValues ? '留空则不更新' : undefined}
        >
          <Input.Password
            placeholder={
              initialValues ? '输入新的API Secret或留空' : '输入API Secret'
            }
          />
        </Form.Item>
      )}

      {/* 自定义端点 */}
      {currentProvider?.supports_custom_endpoint && (
        <Form.Item name="endpoint" label="API端点">
          <Input placeholder={currentProvider.default_endpoint} />
        </Form.Item>
      )}

      {/* 高级设置 */}
      <Collapse
        ghost
        items={[
          {
            key: 'advanced',
            label: '高级设置',
            children: (
              <div className="space-y-4">
                <Form.Item name="temperature" label="Temperature">
                  <InputNumber
                    min={0}
                    max={2}
                    step={0.1}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item name="max_tokens" label="Max Tokens">
                  <InputNumber
                    min={1}
                    max={128000}
                    style={{ width: '100%' }}
                  />
                </Form.Item>

                <Form.Item name="timeout" label="超时时间 (秒)">
                  <InputNumber min={1} max={600} style={{ width: '100%' }} />
                </Form.Item>

                <Form.Item
                  name="is_default"
                  label="设为默认"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </div>
            ),
          },
        ]}
      />

      {/* 按钮 */}
      <Form.Item className="mb-0 mt-4">
        <Space className="w-full justify-end">
          <Button onClick={onCancel}>取消</Button>
          <Button type="primary" htmlType="submit" loading={submitting}>
            {initialValues ? '更新' : '创建'}
          </Button>
        </Space>
      </Form.Item>
    </Form>
  )
}
