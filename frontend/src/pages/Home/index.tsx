import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Button, Table, Tag, Progress, Space, Tooltip, Badge } from 'antd'
import { Link } from 'react-router-dom'
import {
  FileTextOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  CheckCircleOutlined,
  PlusOutlined,
  ArrowRightOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  ApiOutlined,
  ClockCircleOutlined,
  RiseOutlined,
  LineChartOutlined,
  AppstoreOutlined,
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

// 功能卡片配置
const FEATURE_CARDS = [
  {
    key: 'upload',
    title: '上传国标',
    description: '上传PDF/Word国标文档，自动识别标准信息',
    icon: <PlusOutlined className="text-2xl" />,
    link: '/standards/upload',
    color: '#3462FE',
    bgColor: '#EEF2FF',
  },
  {
    key: 'material',
    title: '物料梳理',
    description: '输入非结构化物料描述，智能提取结构化信息',
    icon: <ExperimentOutlined className="text-2xl" />,
    link: '/material-parse',
    color: '#9D34FE',
    bgColor: '#F5EEFF',
  },
  {
    key: 'knowledge',
    title: '知识图谱',
    description: '可视化展示国标知识图谱，探索节点关系',
    icon: <AppstoreOutlined className="text-2xl" />,
    link: '/knowledge-graph',
    color: '#52c41a',
    bgColor: '#F0FFF0',
  },
  {
    key: 'observability',
    title: '执行日志',
    description: '查看物料梳理执行记录，分析执行Trace',
    icon: <LineChartOutlined className="text-2xl" />,
    link: '/observability',
    color: '#faad14',
    bgColor: '#FFFBE6',
  },
]

export default function Home() {
  const [standards, setStandards] = useState<Standard[]>([])
  const [skills, setSkills] = useState<Skill[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [standardsTotal, setStandardsTotal] = useState(0)
  const [skillsTotal, setSkillsTotal] = useState(0)
  const [systemHealth, setSystemHealth] = useState({
    api: true,
    database: true,
    neo4j: false, // Neo4j暂未连接
  })

  useEffect(() => {
    loadData()
    checkSystemHealth()
  }, [])

  const loadData = async () => {
    try {
      const [standardsRes, skillsRes, metricsRes] = await Promise.all([
        standardsApi.list({ page: 1, page_size: 5 }),
        skillsApi.list({ page: 1, page_size: 5 }),
        observabilityApi.metrics(),
      ])
      setStandards((standardsRes as { items: Standard[]; total: number }).items || [])
      setStandardsTotal((standardsRes as { total: number }).total || 0)
      setSkills((skillsRes as { items: Skill[]; total: number }).items || [])
      setSkillsTotal((skillsRes as { total: number }).total || 0)
      setMetrics(metricsRes as Metrics)
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const checkSystemHealth = async () => {
    // 简单的健康检查
    try {
      await observabilityApi.metrics()
      setSystemHealth(prev => ({ ...prev, api: true, database: true }))
    } catch {
      setSystemHealth(prev => ({ ...prev, api: false }))
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

  const healthStatus = Object.values(systemHealth).filter(Boolean).length
  const healthTotal = Object.keys(systemHealth).length

  return (
    <div className="space-y-6">
      {/* 欢迎横幅 */}
      <div className="brand-gradient rounded-lg p-6 text-white relative overflow-hidden">
        <div className="relative z-10">
          <h1 className="text-2xl font-bold mb-2">GBSkillEngine</h1>
          <p className="text-white/80 mb-4">
            MRO国标技能引擎平台 - 国标 → Skills 编译 → 知识图谱 → 物料标准化梳理
          </p>
          <div className="flex gap-3 flex-wrap">
            <Link to="/standards/upload">
              <Button type="primary" icon={<PlusOutlined />} ghost>
                上传国标
              </Button>
            </Link>
            <Link to="/material-parse">
              <Button icon={<ExperimentOutlined />} ghost className="text-white border-white hover:text-white hover:border-white">
                物料梳理
              </Button>
            </Link>
            <Link to="/knowledge-graph">
              <Button icon={<AppstoreOutlined />} ghost className="text-white border-white hover:text-white hover:border-white">
                知识图谱
              </Button>
            </Link>
          </div>
        </div>
        {/* 背景装饰 */}
        <div className="absolute right-0 top-0 opacity-10">
          <ThunderboltOutlined style={{ fontSize: 200 }} />
        </div>
      </div>

      {/* 功能入口卡片 */}
      <Row gutter={16}>
        {FEATURE_CARDS.map(card => (
          <Col span={6} key={card.key}>
            <Link to={card.link}>
              <Card 
                hoverable 
                className="h-full transition-all hover:shadow-lg"
                styles={{ body: { padding: '20px' } }}
              >
                <div className="flex items-start gap-4">
                  <div 
                    className="w-12 h-12 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: card.bgColor, color: card.color }}
                  >
                    {card.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-base mb-1">{card.title}</div>
                    <div className="text-gray-400 text-sm">{card.description}</div>
                  </div>
                </div>
                <div className="mt-3 text-right">
                  <ArrowRightOutlined style={{ color: card.color }} />
                </div>
              </Card>
            </Link>
          </Col>
        ))}
      </Row>

      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <span className="flex items-center gap-2">
                  <FileTextOutlined />
                  国标数量
                </span>
              }
              value={standardsTotal}
              valueStyle={{ color: '#3462FE' }}
              suffix={
                <Link to="/standards" className="text-sm ml-2">
                  查看全部 <ArrowRightOutlined />
                </Link>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <span className="flex items-center gap-2">
                  <ThunderboltOutlined />
                  Skills数量
                </span>
              }
              value={skillsTotal}
              valueStyle={{ color: '#9D34FE' }}
              suffix={
                <Link to="/skills" className="text-sm ml-2">
                  查看全部 <ArrowRightOutlined />
                </Link>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <span className="flex items-center gap-2">
                  <RiseOutlined />
                  执行次数
                </span>
              }
              value={metrics?.total_executions || 0}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <span className="text-sm text-gray-400 ml-2">
                  成功率 {((metrics?.success_rate || 0) * 100).toFixed(1)}%
                </span>
              }
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title={
                <span className="flex items-center gap-2">
                  <ClockCircleOutlined />
                  平均耗时
                </span>
              }
              value={metrics?.avg_execution_time_ms?.toFixed(0) || 0}
              suffix="ms"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 系统健康状态 */}
      <Card 
        title={
          <div className="flex items-center gap-2">
            <CloudServerOutlined />
            <span>系统状态</span>
          </div>
        }
        extra={
          <Badge 
            status={healthStatus === healthTotal ? 'success' : healthStatus > 0 ? 'warning' : 'error'} 
            text={`${healthStatus}/${healthTotal} 服务正常`} 
          />
        }
        size="small"
      >
        <Row gutter={16}>
          <Col span={8}>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <Space>
                <ApiOutlined className="text-lg" />
                <span>API服务</span>
              </Space>
              <Tooltip title={systemHealth.api ? '运行正常' : '服务异常'}>
                <Badge status={systemHealth.api ? 'success' : 'error'} />
              </Tooltip>
            </div>
          </Col>
          <Col span={8}>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <Space>
                <DatabaseOutlined className="text-lg" />
                <span>PostgreSQL</span>
              </Space>
              <Tooltip title={systemHealth.database ? '连接正常' : '连接异常'}>
                <Badge status={systemHealth.database ? 'success' : 'error'} />
              </Tooltip>
            </div>
          </Col>
          <Col span={8}>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <Space>
                <AppstoreOutlined className="text-lg" />
                <span>Neo4j</span>
              </Space>
              <Tooltip title={systemHealth.neo4j ? '连接正常' : '使用Mock数据'}>
                <Badge status={systemHealth.neo4j ? 'success' : 'warning'} />
              </Tooltip>
            </div>
          </Col>
        </Row>
        
        {/* 系统概览 */}
        <div className="mt-4 pt-4 border-t">
          <Row gutter={16}>
            <Col span={8}>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{standardsTotal}</div>
                <div className="text-gray-500 text-sm">已录入国标</div>
              </div>
            </Col>
            <Col span={8}>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{skillsTotal}</div>
                <div className="text-gray-500 text-sm">已编译Skill</div>
              </div>
            </Col>
            <Col span={8}>
              <div className="text-center">
                <Progress 
                  type="circle" 
                  percent={Math.round((metrics?.success_rate || 0) * 100)} 
                  size={60}
                  strokeColor="#52c41a"
                />
                <div className="text-gray-500 text-sm mt-1">梳理成功率</div>
              </div>
            </Col>
          </Row>
        </div>
      </Card>

      {/* 数据列表 */}
      <Row gutter={16}>
        <Col span={12}>
          <Card
            title={
              <div className="flex items-center gap-2">
                <FileTextOutlined />
                <span>最近上传的国标</span>
              </div>
            }
            extra={<Link to="/standards">查看全部 <ArrowRightOutlined /></Link>}
          >
            <Table
              columns={standardColumns}
              dataSource={standards}
              rowKey="id"
              pagination={false}
              size="small"
              loading={loading}
              locale={{ emptyText: '暂无数据' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title={
              <div className="flex items-center gap-2">
                <ThunderboltOutlined />
                <span>最近创建的Skill</span>
              </div>
            }
            extra={<Link to="/skills">查看全部 <ArrowRightOutlined /></Link>}
          >
            <Table
              columns={skillColumns}
              dataSource={skills}
              rowKey="id"
              pagination={false}
              size="small"
              loading={loading}
              locale={{ emptyText: '暂无数据' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
