import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, Button, Tag, Table, message, Descriptions, Statistic, Row, Col, 
  Progress, Tabs, Select, Alert
} from 'antd'
import { ArrowLeftOutlined, ReloadOutlined, DownloadOutlined } from '@ant-design/icons'
import { benchmarkApi } from '@/services/api'

interface BenchmarkRun {
  id: number
  run_code: string
  run_name?: string
  dataset_id: number
  status: string
  total_cases: number
  completed_cases: number
  progress: number
  metrics?: BenchmarkMetrics
  created_at: string
  completed_at?: string
}

interface BenchmarkMetrics {
  overall: {
    total_cases: number
    accuracy: number
    partial_accuracy: number
    skill_match_rate: number
    avg_confidence: number
    avg_score: number
    avg_execution_time_ms: number
  }
  by_difficulty: Record<string, {
    count: number
    accuracy: number
    avg_score: number
  }>
  by_attribute: Record<string, {
    total: number
    exact_match: number
    within_tolerance: number
    missing_rate: number
  }>
  by_status: Record<string, number>
}

interface BenchmarkResult {
  id: number
  case_id: number
  case_code?: string
  input_text?: string
  difficulty?: string
  actual_skill_id?: string
  actual_attributes?: Record<string, unknown>
  skill_match?: boolean
  attribute_scores?: Record<string, {
    expected: unknown
    actual: unknown
    match: boolean
    score: number
    match_type: string
  }>
  overall_score?: number
  status: string
  error_message?: string
  execution_time_ms?: number
}

export default function RunDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const runId = parseInt(id || '0')
  
  const [run, setRun] = useState<BenchmarkRun | null>(null)
  const [results, setResults] = useState<BenchmarkResult[]>([])
  const [loading, setLoading] = useState(true)
  const [resultsLoading, setResultsLoading] = useState(false)
  
  const [activeTab, setActiveTab] = useState('overview')
  const [resultPage, setResultPage] = useState(1)
  const [resultTotal, setResultTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [difficultyFilter, setDifficultyFilter] = useState<string | undefined>()

  useEffect(() => {
    if (runId) {
      loadRun()
    }
  }, [runId])

  useEffect(() => {
    if (activeTab === 'results') {
      loadResults()
    }
  }, [activeTab, resultPage, statusFilter, difficultyFilter])

  const loadRun = async () => {
    setLoading(true)
    try {
      const res = await benchmarkApi.getRun(runId) as BenchmarkRun
      setRun(res)
    } catch (error) {
      message.error('加载评测详情失败')
    } finally {
      setLoading(false)
    }
  }

  const loadResults = async () => {
    setResultsLoading(true)
    try {
      const params: Record<string, unknown> = { page: resultPage, page_size: 20 }
      if (statusFilter) params.status = statusFilter
      if (difficultyFilter) params.difficulty = difficultyFilter
      
      const res = await benchmarkApi.getRunResults(runId, params) as {
        items: BenchmarkResult[]
        total: number
      }
      setResults(res.items || [])
      setResultTotal(res.total || 0)
    } catch (error) {
      message.error('加载结果失败')
    } finally {
      setResultsLoading(false)
    }
  }

  const resultColumns = [
    {
      title: '用例',
      key: 'case',
      width: 200,
      render: (_: unknown, record: BenchmarkResult) => (
        <div>
          <div className="font-medium">{record.case_code}</div>
          <div className="text-gray-400 text-xs truncate" style={{ maxWidth: 180 }}>
            {record.input_text}
          </div>
        </div>
      )
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          success: { color: 'success', text: '成功' },
          partial: { color: 'warning', text: '部分' },
          failed: { color: 'error', text: '失败' },
          error: { color: 'default', text: '错误' },
        }
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      }
    },
    {
      title: 'Skill匹配',
      dataIndex: 'skill_match',
      key: 'skill_match',
      width: 80,
      render: (match: boolean | null) => {
        if (match === null || match === undefined) return '-'
        return match ? <Tag color="green">匹配</Tag> : <Tag color="red">不匹配</Tag>
      }
    },
    {
      title: '得分',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 100,
      render: (score: number | undefined) => {
        if (score === undefined || score === null) return '-'
        const percent = Math.round(score * 100)
        return (
          <Progress 
            percent={percent} 
            size="small" 
            status={percent >= 80 ? 'success' : percent >= 50 ? 'normal' : 'exception'}
          />
        )
      }
    },
    {
      title: '耗时',
      dataIndex: 'execution_time_ms',
      key: 'execution_time_ms',
      width: 80,
      render: (ms: number) => ms ? `${ms}ms` : '-'
    },
    {
      title: '错误信息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 150,
      ellipsis: true,
      render: (msg: string) => msg ? <span className="text-red-500">{msg}</span> : '-'
    }
  ]

  if (loading || !run) {
    return <Card loading={loading}>加载中...</Card>
  }

  const metrics = run.metrics

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex justify-between items-start mb-4">
          <div>
            <Button 
              type="link" 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate(`/benchmark/datasets/${run.dataset_id}`)}
              className="pl-0 mb-2"
            >
              返回数据集
            </Button>
            <h2 className="text-xl font-semibold mb-2">{run.run_name || run.run_code}</h2>
            <p className="text-gray-500">{run.run_code}</p>
          </div>
          <Tag color={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'error' : 'processing'}>
            {run.status}
          </Tag>
        </div>
        
        <Descriptions column={4} size="small">
          <Descriptions.Item label="总用例数">{run.total_cases}</Descriptions.Item>
          <Descriptions.Item label="已完成">{run.completed_cases}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(run.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="完成时间">
            {run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {metrics && (
        <Card title="评测指标概览">
          <Row gutter={[16, 16]}>
            <Col span={4}>
              <Statistic 
                title="准确率" 
                value={(metrics.overall.accuracy * 100).toFixed(1)} 
                suffix="%" 
                valueStyle={{ color: metrics.overall.accuracy >= 0.8 ? '#52c41a' : '#faad14' }}
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="部分准确率" 
                value={(metrics.overall.partial_accuracy * 100).toFixed(1)} 
                suffix="%" 
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="Skill匹配率" 
                value={(metrics.overall.skill_match_rate * 100).toFixed(1)} 
                suffix="%" 
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="平均得分" 
                value={(metrics.overall.avg_score * 100).toFixed(1)} 
                suffix="%" 
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="平均置信度" 
                value={(metrics.overall.avg_confidence * 100).toFixed(1)} 
                suffix="%" 
              />
            </Col>
            <Col span={4}>
              <Statistic 
                title="平均耗时" 
                value={metrics.overall.avg_execution_time_ms.toFixed(0)} 
                suffix="ms" 
              />
            </Col>
          </Row>

          <div className="mt-6">
            <h4 className="font-medium mb-3">按难度分布</h4>
            <Row gutter={16}>
              {Object.entries(metrics.by_difficulty).map(([diff, data]) => (
                <Col span={6} key={diff}>
                  <Card size="small">
                    <Statistic 
                      title={<Tag color={
                        diff === 'easy' ? 'green' : 
                        diff === 'medium' ? 'blue' : 
                        diff === 'hard' ? 'orange' : 'red'
                      }>{diff}</Tag>}
                      value={(data.accuracy * 100).toFixed(1)}
                      suffix={`% (${data.count})`}
                    />
                  </Card>
                </Col>
              ))}
            </Row>
          </div>

          {Object.keys(metrics.by_attribute).length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium mb-3">按属性分布</h4>
              <Table
                dataSource={Object.entries(metrics.by_attribute).map(([attr, data]) => ({
                  attribute: attr,
                  ...data
                }))}
                columns={[
                  { title: '属性', dataIndex: 'attribute', key: 'attribute' },
                  { title: '总数', dataIndex: 'total', key: 'total', width: 80 },
                  { 
                    title: '精确匹配率', 
                    dataIndex: 'exact_match', 
                    key: 'exact_match',
                    render: (v: number) => `${(v * 100).toFixed(1)}%`
                  },
                  { 
                    title: '容差匹配率', 
                    dataIndex: 'within_tolerance', 
                    key: 'within_tolerance',
                    render: (v: number) => `${(v * 100).toFixed(1)}%`
                  },
                  { 
                    title: '缺失率', 
                    dataIndex: 'missing_rate', 
                    key: 'missing_rate',
                    render: (v: number) => <span className={v > 0.1 ? 'text-red-500' : ''}>{(v * 100).toFixed(1)}%</span>
                  },
                ]}
                rowKey="attribute"
                pagination={false}
                size="small"
              />
            </div>
          )}

          <div className="mt-6">
            <h4 className="font-medium mb-3">按状态分布</h4>
            <Row gutter={16}>
              {Object.entries(metrics.by_status).map(([status, count]) => (
                <Col span={6} key={status}>
                  <Statistic 
                    title={status}
                    value={count}
                    valueStyle={{ 
                      color: status === 'success' ? '#52c41a' : 
                             status === 'failed' ? '#f5222d' : '#faad14'
                    }}
                  />
                </Col>
              ))}
            </Row>
          </div>
        </Card>
      )}

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane tab="概览" key="overview">
            {!metrics && (
              <Alert message="评测尚未完成，暂无指标数据" type="info" />
            )}
          </Tabs.TabPane>
          
          <Tabs.TabPane tab={`详细结果 (${run.completed_cases})`} key="results">
            <div className="mb-4 flex justify-between">
              <div className="flex gap-2">
                <Select
                  placeholder="状态筛选"
                  style={{ width: 120 }}
                  value={statusFilter}
                  onChange={setStatusFilter}
                  allowClear
                  options={[
                    { value: 'success', label: '成功' },
                    { value: 'partial', label: '部分' },
                    { value: 'failed', label: '失败' },
                    { value: 'error', label: '错误' },
                  ]}
                />
                <Select
                  placeholder="难度筛选"
                  style={{ width: 120 }}
                  value={difficultyFilter}
                  onChange={setDifficultyFilter}
                  allowClear
                  options={[
                    { value: 'easy', label: 'Easy' },
                    { value: 'medium', label: 'Medium' },
                    { value: 'hard', label: 'Hard' },
                    { value: 'adversarial', label: 'Adversarial' },
                  ]}
                />
              </div>
              <Button icon={<ReloadOutlined />} onClick={loadResults}>刷新</Button>
            </div>
            <Table
              columns={resultColumns}
              dataSource={results}
              rowKey="id"
              loading={resultsLoading}
              pagination={{
                current: resultPage,
                pageSize: 20,
                total: resultTotal,
                onChange: setResultPage
              }}
              size="small"
              expandable={{
                expandedRowRender: (record) => (
                  <div className="p-4 bg-gray-50">
                    <h4 className="font-medium mb-2">属性匹配详情</h4>
                    {record.attribute_scores && Object.entries(record.attribute_scores).map(([attr, score]) => (
                      <div key={attr} className="flex items-center gap-4 py-1">
                        <span className="w-24 font-medium">{attr}:</span>
                        <span className="w-32">期望: {JSON.stringify(score.expected)}</span>
                        <span className="w-32">实际: {JSON.stringify(score.actual)}</span>
                        <Tag color={score.match ? 'green' : 'red'}>{score.match_type}</Tag>
                        <span>得分: {(score.score * 100).toFixed(0)}%</span>
                      </div>
                    ))}
                  </div>
                )
              }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}
