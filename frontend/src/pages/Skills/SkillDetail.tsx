import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Spin, message, Space, Collapse } from 'antd'
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons'
import { skillsApi } from '@/services/api'

interface Skill {
  id: number
  skill_id: string
  skill_name: string
  domain: string
  priority: number
  applicable_material_types: string[]
  dsl_content: Record<string, unknown>
  dsl_version: string
  status: string
  standard_id: number
  created_at: string
  updated_at: string
}

export default function SkillDetail() {
  const { skillId } = useParams<{ skillId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<Skill | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [skillId])

  const loadData = async () => {
    try {
      const res = await skillsApi.detail(skillId!)
      setData(res as Skill)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  if (!data) {
    return <div>Skill不存在</div>
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    testing: { color: 'blue', text: '测试中' },
    active: { color: 'green', text: '已激活' },
    deprecated: { color: 'red', text: '已停用' },
  }

  const collapseItems = [
    {
      key: 'intent',
      label: '意图识别规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.intentRecognition, null, 2)}
        </pre>
      ),
    },
    {
      key: 'extraction',
      label: '属性抽取规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.attributeExtraction, null, 2)}
        </pre>
      ),
    },
    {
      key: 'rules',
      label: '业务规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.rules, null, 2)}
        </pre>
      ),
    },
    {
      key: 'tables',
      label: '数据表格',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
          {JSON.stringify(data.dsl_content.tables, null, 2)}
        </pre>
      ),
    },
    {
      key: 'category',
      label: '类目映射',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.categoryMapping, null, 2)}
        </pre>
      ),
    },
    {
      key: 'output',
      label: '输出结构',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.outputStructure, null, 2)}
        </pre>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/skills')}
        >
          返回列表
        </Button>
        <Space>
          <Link to={`/skills/${skillId}/edit`}>
            <Button type="primary" icon={<EditOutlined />}>
              编辑DSL
            </Button>
          </Link>
        </Space>
      </div>

      <Card title="Skill详情">
        <Descriptions column={2}>
          <Descriptions.Item label="Skill ID">{data.skill_id}</Descriptions.Item>
          <Descriptions.Item label="名称">{data.skill_name}</Descriptions.Item>
          <Descriptions.Item label="领域">
            <Tag>
              {data.domain === 'pipe' ? '管材' : data.domain === 'fastener' ? '紧固件' : data.domain || '未分类'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[data.status]?.color || 'default'}>
              {statusMap[data.status]?.text || data.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="版本">{data.dsl_version}</Descriptions.Item>
          <Descriptions.Item label="优先级">{data.priority}</Descriptions.Item>
          <Descriptions.Item label="适用物料类型" span={2}>
            {data.applicable_material_types?.map((t) => (
              <Tag key={t}>{t}</Tag>
            ))}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(data.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(data.updated_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="DSL配置">
        <Collapse items={collapseItems} defaultActiveKey={['intent', 'extraction']} />
      </Card>
    </div>
  )
}
