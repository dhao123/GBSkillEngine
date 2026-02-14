import { useEffect, useState } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { 
  Card, Tabs, Button, Space, Tag, Table, message, Popconfirm, 
  Modal, Form, Input, Select, InputNumber, Progress, Descriptions, Statistic, Row, Col
} from 'antd'
import { 
  PlayCircleOutlined, PlusOutlined, DeleteOutlined, 
  ReloadOutlined, ThunderboltOutlined, ArrowLeftOutlined
} from '@ant-design/icons'
import { benchmarkApi, skillsApi } from '@/services/api'

interface Dataset {
  id: number
  dataset_code: string
  dataset_name: string
  description?: string
  skill_id?: number
  source_type: string
  status: string
  total_cases: number
  difficulty_distribution?: Record<string, number>
  created_at: string
}

interface BenchmarkCase {
  id: number
  case_code: string
  input_text: string
  expected_skill_id?: string
  expected_attributes: Record<string, unknown>
  difficulty: string
  source_type: string
  is_active: boolean
  created_at: string
}

interface BenchmarkRun {
  id: number
  run_code: string
  run_name?: string
  status: string
  total_cases: number
  completed_cases: number
  progress: number
  metrics?: {
    overall?: {
      accuracy: number
      skill_match_rate: number
      avg_score: number
    }
  }
  created_at: string
  completed_at?: string
}

interface Skill {
  id: number
  skill_id: string
  skill_name: string
}

export default function DatasetDetail() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const datasetId = parseInt(id || '0')
  
  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [cases, setCases] = useState<BenchmarkCase[]>([])
  const [runs, setRuns] = useState<BenchmarkRun[]>([])
  const [loading, setLoading] = useState(true)
  const [casesLoading, setCasesLoading] = useState(false)
  const [runsLoading, setRunsLoading] = useState(false)
  
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'cases')
  const [casePage, setCasePage] = useState(1)
  const [caseTotal, setCaseTotal] = useState(0)
  
  // 生成数据弹窗
  const [generateModalOpen, setGenerateModalOpen] = useState(false)
  const [generateForm] = Form.useForm()
  const [generating, setGenerating] = useState(false)
  const [skills, setSkills] = useState<Skill[]>([])
  
  // 运行评测弹窗
  const [runModalOpen, setRunModalOpen] = useState(false)
  const [runForm] = Form.useForm()
  const [runningCreate, setRunningCreate] = useState(false)

  useEffect(() => {
    if (datasetId) {
      loadDataset()
      loadSkills()
    }
  }, [datasetId])

  useEffect(() => {
    if (activeTab === 'cases') {
      loadCases()
    } else if (activeTab === 'runs') {
      loadRuns()
    }
  }, [activeTab, casePage])

  const loadDataset = async () => {
    setLoading(true)
    try {
      const res = await benchmarkApi.getDataset(datasetId) as Dataset
      setDataset(res)
    } catch (error) {
      message.error('加载数据集失败')
    } finally {
      setLoading(false)
    }
  }

  const loadSkills = async () => {
    try {
      const res = await skillsApi.list({ page: 1, page_size: 100, status: 'active' }) as {
        items: Skill[]
      }
      setSkills(res.items || [])
    } catch {
      // ignore
    }
  }

  const loadCases = async () => {
    setCasesLoading(true)
    try {
      const res = await benchmarkApi.listCases(datasetId, { page: casePage, page_size: 20 }) as {
        items: BenchmarkCase[]
        total: number
      }
      setCases(res.items || [])
      setCaseTotal(res.total || 0)
    } catch (error) {
      message.error('加载用例失败')
    } finally {
      setCasesLoading(false)
    }
  }

  const loadRuns = async () => {
    setRunsLoading(true)
    try {
      const res = await benchmarkApi.listRuns({ dataset_id: datasetId, page: 1, page_size: 20 }) as {
        items: BenchmarkRun[]
      }
      setRuns(res.items || [])
    } catch (error) {
      message.error('加载评测记录失败')
    } finally {
      setRunsLoading(false)
    }
  }

  const handleGenerate = async (values: Record<string, unknown>) => {
    setGenerating(true)
    try {
      const res = await benchmarkApi.generateCases(datasetId, values) as {
        generated_count: number
        stats: Record<string, unknown>
      }
      message.success(`成功生成 ${res.generated_count} 个测试用例`)
      setGenerateModalOpen(false)
      generateForm.resetFields()
      loadDataset()
      loadCases()
    } catch (error) {
      message.error('生成失败')
    } finally {
      setGenerating(false)
    }
  }

  const handleCreateRun = async (values: Record<string, unknown>) => {
    setRunningCreate(true)
    try {
      const runRes = await benchmarkApi.createRun({
        dataset_id: datasetId,
        ...values
      }) as BenchmarkRun
      
      // 立即执行
      await benchmarkApi.executeRun(runRes.id)
      
      message.success('评测已完成')
      setRunModalOpen(false)
      runForm.resetFields()
      loadRuns()
      setActiveTab('runs')
    } catch (error) {
      message.error('执行失败')
    } finally {
      setRunningCreate(false)
    }
  }

  const handleDeleteCase = async (caseId: number) => {
    try {
      await benchmarkApi.deleteCase(caseId)
      message.success('删除成功')
      loadCases()
      loadDataset()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const caseColumns = [
    {
      title: '用例编码',
      dataIndex: 'case_code',
      key: 'case_code',
      width: 180,
    },
    {
      title: '输入文本',
      dataIndex: 'input_text',
      key: 'input_text',
      width: 300,
      ellipsis: true,
    },
    {
      title: '难度',
      dataIndex: 'difficulty',
      key: 'difficulty',
      width: 80,
      render: (diff: string) => {
        const colorMap: Record<string, string> = {
          easy: 'green',
          medium: 'blue',
          hard: 'orange',
          adversarial: 'red'
        }
        return <Tag color={colorMap[diff] || 'default'}>{diff}</Tag>
      }
    },
    {
      title: '来源',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, string> = {
          seed: '种子',
          table_enum: '表格枚举',
          template: '模板',
          noise: '噪声'
        }
        return <Tag>{typeMap[type] || type}</Tag>
      }
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'default'}>{active ? '启用' : '禁用'}</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: BenchmarkCase) => (
        <Popconfirm title="确定删除?" onConfirm={() => handleDeleteCase(record.id)}>
          <Button type="link" size="small" danger icon={<DeleteOutlined />}>删除</Button>
        </Popconfirm>
      )
    }
  ]

  const runColumns = [
    {
      title: '运行编码',
      dataIndex: 'run_code',
      key: 'run_code',
      width: 200,
    },
    {
      title: '名称',
      dataIndex: 'run_name',
      key: 'run_name',
      width: 200,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string, record: BenchmarkRun) => {
        if (status === 'running') {
          return <Progress percent={Math.round(record.progress)} size="small" />
        }
        const statusMap: Record<string, { color: string; text: string }> = {
          pending: { color: 'default', text: '等待中' },
          running: { color: 'processing', text: '运行中' },
          completed: { color: 'success', text: '已完成' },
          failed: { color: 'error', text: '失败' },
        }
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      }
    },
    {
      title: '准确率',
      key: 'accuracy',
      width: 100,
      render: (_: unknown, record: BenchmarkRun) => {
        if (record.metrics?.overall?.accuracy !== undefined) {
          return <span className="font-medium">{(record.metrics.overall.accuracy * 100).toFixed(1)}%</span>
        }
        return '-'
      }
    },
    {
      title: '用例数',
      key: 'cases',
      width: 120,
      render: (_: unknown, record: BenchmarkRun) => (
        <span>{record.completed_cases} / {record.total_cases}</span>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: BenchmarkRun) => (
        <Button 
          type="link" 
          size="small"
          onClick={() => navigate(`/benchmark/runs/${record.id}`)}
        >
          查看详情
        </Button>
      )
    }
  ]

  if (loading || !dataset) {
    return <Card loading={loading}>加载中...</Card>
  }

  const diffDist = dataset.difficulty_distribution || {}

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex justify-between items-start mb-4">
          <div>
            <Button 
              type="link" 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/benchmark/datasets')}
              className="pl-0 mb-2"
            >
              返回列表
            </Button>
            <h2 className="text-xl font-semibold mb-2">{dataset.dataset_name}</h2>
            <p className="text-gray-500">{dataset.dataset_code}</p>
          </div>
          <Space>
            <Button icon={<PlusOutlined />} onClick={() => setGenerateModalOpen(true)}>
              生成数据
            </Button>
            <Button 
              type="primary" 
              icon={<ThunderboltOutlined />}
              onClick={() => setRunModalOpen(true)}
              disabled={dataset.total_cases === 0}
            >
              运行评测
            </Button>
          </Space>
        </div>
        
        <Descriptions column={4} size="small">
          <Descriptions.Item label="状态">
            <Tag color={dataset.status === 'ready' ? 'green' : 'default'}>
              {dataset.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="来源类型">{dataset.source_type}</Descriptions.Item>
          <Descriptions.Item label="总用例数">{dataset.total_cases}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(dataset.created_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>

        {dataset.total_cases > 0 && (
          <Row gutter={16} className="mt-4">
            <Col span={6}>
              <Statistic 
                title="简单 (Easy)" 
                value={diffDist.easy || 0} 
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="中等 (Medium)" 
                value={diffDist.medium || 0} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="困难 (Hard)" 
                value={diffDist.hard || 0} 
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
            <Col span={6}>
              <Statistic 
                title="对抗 (Adversarial)" 
                value={diffDist.adversarial || 0} 
                valueStyle={{ color: '#f5222d' }}
              />
            </Col>
          </Row>
        )}
      </Card>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane tab={`测试用例 (${dataset.total_cases})`} key="cases">
            <div className="mb-4 flex justify-end">
              <Button icon={<ReloadOutlined />} onClick={loadCases}>刷新</Button>
            </div>
            <Table
              columns={caseColumns}
              dataSource={cases}
              rowKey="id"
              loading={casesLoading}
              pagination={{
                current: casePage,
                pageSize: 20,
                total: caseTotal,
                onChange: setCasePage
              }}
              size="small"
            />
          </Tabs.TabPane>
          
          <Tabs.TabPane tab="评测记录" key="runs">
            <div className="mb-4 flex justify-end">
              <Button icon={<ReloadOutlined />} onClick={loadRuns}>刷新</Button>
            </div>
            <Table
              columns={runColumns}
              dataSource={runs}
              rowKey="id"
              loading={runsLoading}
              pagination={false}
              size="small"
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>

      {/* 生成数据弹窗 */}
      <Modal
        title="自动生成测试数据"
        open={generateModalOpen}
        onCancel={() => setGenerateModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form form={generateForm} layout="vertical" onFinish={handleGenerate}>
          <Form.Item
            name="skill_id"
            label="选择 Skill"
            rules={[{ required: true, message: '请选择Skill' }]}
          >
            <Select
              placeholder="选择要从中生成数据的Skill"
              options={skills.map(s => ({ value: s.id, label: `${s.skill_id} - ${s.skill_name}` }))}
            />
          </Form.Item>
          <Form.Item
            name="count"
            label="生成数量"
            initialValue={100}
          >
            <InputNumber min={1} max={10000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="include_noise"
            label="包含噪声变体"
            initialValue={true}
          >
            <Select options={[
              { value: true, label: '是' },
              { value: false, label: '否' },
            ]} />
          </Form.Item>
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => setGenerateModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={generating}>
                开始生成
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 运行评测弹窗 */}
      <Modal
        title="运行评测"
        open={runModalOpen}
        onCancel={() => setRunModalOpen(false)}
        footer={null}
        width={450}
      >
        <Form form={runForm} layout="vertical" onFinish={handleCreateRun}>
          <Form.Item
            name="run_name"
            label="评测名称"
          >
            <Input placeholder="可选，如：首次完整评测" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="可选描述..." />
          </Form.Item>
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => setRunModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={runningCreate}>
                开始评测
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
