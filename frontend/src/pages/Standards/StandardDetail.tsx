import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Spin, message, Space } from 'antd'
import { ArrowLeftOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { standardsApi } from '@/services/api'

interface Standard {
  id: number
  standard_code: string
  standard_name: string
  version_year: string
  domain: string
  product_scope: string
  file_path: string
  file_type: string
  status: string
  created_at: string
  updated_at: string
}

export default function StandardDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<Standard | null>(null)
  const [loading, setLoading] = useState(true)
  const [compiling, setCompiling] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const res = await standardsApi.detail(Number(id))
      setData(res as Standard)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCompile = async () => {
    setCompiling(true)
    try {
      const res = await standardsApi.compile(Number(id)) as { skill_id: string }
      message.success('编译成功')
      loadData()
      navigate(`/skills/${res.skill_id}`)
    } catch (error) {
      message.error('编译失败')
    } finally {
      setCompiling(false)
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
    return <div>国标不存在</div>
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    uploaded: { color: 'blue', text: '已上传' },
    compiled: { color: 'green', text: '已编译' },
    published: { color: 'purple', text: '已发布' },
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/standards')}
        >
          返回列表
        </Button>
        <Space>
          {data.status === 'uploaded' && (
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={compiling}
              onClick={handleCompile}
            >
              编译为Skill
            </Button>
          )}
          {data.status === 'compiled' && (
            <Link to={`/skills/skill_${data.standard_code.replace(/[\/\.\-]/g, '_').toLowerCase()}`}>
              <Button type="primary" icon={<ThunderboltOutlined />}>
                查看Skill
              </Button>
            </Link>
          )}
        </Space>
      </div>

      <Card title="国标详情">
        <Descriptions column={2}>
          <Descriptions.Item label="国标编号">{data.standard_code}</Descriptions.Item>
          <Descriptions.Item label="标准名称">{data.standard_name}</Descriptions.Item>
          <Descriptions.Item label="版本年份">{data.version_year || '-'}</Descriptions.Item>
          <Descriptions.Item label="适用领域">
            <Tag>
              {data.domain === 'pipe' ? '管材' : data.domain === 'fastener' ? '紧固件' : data.domain || '未分类'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[data.status]?.color || 'default'}>
              {statusMap[data.status]?.text || data.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="文件类型">{data.file_type?.toUpperCase() || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(data.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(data.updated_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="产品范围" span={2}>
            {data.product_scope || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}
