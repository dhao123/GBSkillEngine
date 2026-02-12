import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Button, Table, Tag } from 'antd'
import { Link } from 'react-router-dom'
import {
  FileTextOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { standardsApi, skillsApi, observabilityApi } from '@/services/api'

interface Standard {
  id: number
  standard_code: string
  standard_name: string
  status: string
  created_at: string
}

interface Skill {
  id: number
  skill_id: string
  skill_name: string
  domain: string
  status: string
}

interface Metrics {
  total_executions: number
  success_count: number
  success_rate: number
  avg_confidence: number
  avg_execution_time_ms: number
}

export default function Home() {
  const [standards, setStandards] = useState<Standard[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [standardsRes, skillsRes, metricsRes] = await Promise.all([
        standardsApi.list({ page: 1, page_size: 5 }),
        skillsApi.list({ page: 1, page_size: 5 }),
        observabilityApi.metrics(),
      ])
      setStandards((standardsRes as { items: Standard[] }).items || [])
      setSkills((skillsRes as { items: Skill[] }).items || [])
      setMetrics(metricsRes as Metrics)
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const standardColumns = [
    { title: '国标编号', dataIndex: 'standard_code', key: 'standard_code' },
    { title: '标准名称', dataIndex: 'standard_name', key: 'standard_name', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'compiled' ? 'green' : status === 'uploaded' ? 'blue' : 'default'}>
          {status === 'compiled' ? '已编译' : status === 'uploaded' ? '已上传' : '草稿'}
        </Tag>
      ),
    },
  ]

  const skillColumns = [
    { title: 'Skill ID', dataIndex: 'skill_id', key: 'skill_id' },
    { title: '名称', dataIndex: 'skill_name', key: 'skill_name', ellipsis: true },
    { title: '领域', dataIndex: 'domain', key: 'domain' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : status === 'draft' ? 'blue' : 'default'}>
          {status === 'active' ? '已激活' : status === 'draft' ? '草稿' : '停用'}
        </Tag>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      {/* 欢迎横幅 */}
      <div className="brand-gradient rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">GBSkillEngine</h1>
        <p className="text-white/80">
          MRO国标技能引擎平台 - 国标 → Skill 编译 → 知识图谱 → 物料标准化梳理
        </p>
        <div className="mt-4 space-x-4">
          <Link to="/standards/upload">
            <Button icon={<PlusOutlined />}>上传国标</Button>
          </Link>
          <Link to="/material-parse">
            <Button icon={<ExperimentOutlined />}>物料梳理</Button>
          </Link>
        </div>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="国标数量"
              value={standards.length}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3462FE' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Skill数量"
              value={skills.length}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#9D34FE' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="执行次数"
              value={metrics?.total_executions || 0}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="成功率"
              value={((metrics?.success_rate || 0) * 100).toFixed(1)}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 数据列表 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card
            title="最近上传的国标"
            extra={<Link to="/standards">查看全部</Link>}
          >
            <Table
              columns={standardColumns}
              dataSource={standards}
              rowKey="id"
              pagination={false}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="最近创建的Skill"
            extra={<Link to="/skills">查看全部</Link>}
          >
            <Table
              columns={skillColumns}
              dataSource={skills}
              rowKey="id"
              pagination={false}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
