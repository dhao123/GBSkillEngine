import { useState, useEffect, useCallback } from 'react'
import { Card, Spin, Select, Statistic, Row, Col, Table, Tag, Empty } from 'antd'
import {
  ThunderboltOutlined,
  FieldTimeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { Line, DualAxes } from '@ant-design/charts'
import { settingsApi } from '../../services/api'

// ==================== 类型定义 ====================

interface UsageTrendPoint {
  date: string
  total_tokens: number
  prompt_tokens: number
  completion_tokens: number
  total_calls: number
  success_calls: number
  failed_calls: number
  avg_latency_ms: number
}

interface UsageSummary {
  total_calls: number
  total_tokens: number
  total_prompt_tokens: number
  total_completion_tokens: number
  avg_latency_ms: number
  success_rate: number
  by_provider?: Record<string, { calls: number; tokens: number }>
  by_model?: Record<string, { calls: number; tokens: number }>
}

interface UsageMonitorResponse {
  summary: UsageSummary
  trend: UsageTrendPoint[]
}

interface UsageLog {
  id: number
  provider: string
  model_name: string
  caller: string | null
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  latency_ms: number
  success: boolean
  error_message: string | null
  created_at: string
}

interface UsageLogListResponse {
  total: number
  items: UsageLog[]
}

const PROVIDER_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  zkh: '震坤行',
  local: '本地模型',
}

const PROVIDER_COLORS: Record<string, string> = {
  openai: '#10a37f',
  anthropic: '#d97706',
  zkh: '#7c3aed',
  local: '#6b7280',
}

// ==================== 组件 ====================

export default function UsageMonitor() {
  const [loading, setLoading] = useState(false)
  const [days, setDays] = useState(30)
  const [monitorData, setMonitorData] = useState<UsageMonitorResponse | null>(null)
  const [logs, setLogs] = useState<UsageLog[]>([])
  const [logsTotal, setLogsTotal] = useState(0)
  const [logsPage, setLogsPage] = useState(1)

  const loadMonitorData = useCallback(async () => {
    setLoading(true)
    try {
      const [monitor, logRes] = await Promise.all([
        settingsApi.getUsageMonitor<UsageMonitorResponse>({ days }),
        settingsApi.getUsageLogs<UsageLogListResponse>({ skip: 0, limit: 10 }),
      ])
      setMonitorData(monitor)
      setLogs(logRes.items)
      setLogsTotal(logRes.total)
      setLogsPage(1)
    } catch (error) {
      console.error('加载监控数据失败:', error)
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    loadMonitorData()
  }, [loadMonitorData])

  const handlePageChange = async (page: number) => {
    try {
      const res = await settingsApi.getUsageLogs<UsageLogListResponse>({
        skip: (page - 1) * 10,
        limit: 10,
      })
      setLogs(res.items)
      setLogsTotal(res.total)
      setLogsPage(page)
    } catch (error) {
      console.error('加载日志失败:', error)
    }
  }

  const summary = monitorData?.summary
  const trend = monitorData?.trend || []

  // Token 趋势折线图数据：将每个日期的 prompt/completion 分别展开为两条折线
  const tokenTrendData = trend.flatMap((item) => [
    { date: item.date, type: 'Prompt Tokens', tokens: item.prompt_tokens },
    { date: item.date, type: 'Completion Tokens', tokens: item.completion_tokens },
  ])

  const tokenLineConfig = {
    data: tokenTrendData,
    xField: 'date',
    yField: 'tokens',
    colorField: 'type',
    smooth: true,
    height: 300,
    scale: {
      color: { range: ['#1677ff', '#52c41a'] },
    },
    axis: {
      x: { title: '日期' },
      y: { title: 'Tokens' },
    },
    tooltip: {
      channel: 'y',
    },
  }

  // 延迟 + 调用次数双轴图数据
  const latencyTrendData = trend.map((item) => ({
    date: item.date,
    avg_latency_ms: item.avg_latency_ms,
    total_calls: item.total_calls,
  }))

  const dualAxesConfig = {
    data: latencyTrendData,
    xField: 'date',
    height: 300,
    children: [
      {
        type: 'interval' as const,
        yField: 'total_calls',
        style: { fill: '#e8e8e8', fillOpacity: 0.6 },
        axis: {
          y: {
            title: '调用次数',
            position: 'right' as const,
          },
        },
      },
      {
        type: 'line' as const,
        yField: 'avg_latency_ms',
        smooth: true,
        style: { stroke: '#ff4d4f', lineWidth: 2 },
        axis: {
          y: {
            title: '平均延迟 (ms)',
            position: 'left' as const,
          },
        },
      },
    ],
  }

  // 调用记录表格列
  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (val: string) => val ? new Date(val).toLocaleString('zh-CN') : '-',
    },
    {
      title: '供应商',
      dataIndex: 'provider',
      key: 'provider',
      width: 100,
      render: (val: string) => (
        <Tag color={PROVIDER_COLORS[val] || '#6b7280'}>
          {PROVIDER_NAMES[val] || val}
        </Tag>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
      width: 160,
      ellipsis: true,
    },
    {
      title: 'Tokens',
      dataIndex: 'total_tokens',
      key: 'total_tokens',
      width: 90,
      render: (val: number) => val?.toLocaleString() || '0',
    },
    {
      title: '延迟',
      dataIndex: 'latency_ms',
      key: 'latency_ms',
      width: 90,
      render: (val: number) => val != null ? `${val}ms` : '-',
    },
    {
      title: '状态',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (val: boolean) =>
        val ? (
          <Tag color="green">成功</Tag>
        ) : (
          <Tag color="red">失败</Tag>
        ),
    },
    {
      title: '调用方',
      dataIndex: 'caller',
      key: 'caller',
      width: 120,
      ellipsis: true,
      render: (val: string | null) => val || '-',
    },
  ]

  // 供应商分布
  const providerStats = summary?.by_provider
    ? Object.entries(summary.by_provider).map(([key, val]) => ({
        provider: PROVIDER_NAMES[key] || key,
        calls: val.calls,
        tokens: val.tokens,
        color: PROVIDER_COLORS[key] || '#6b7280',
      }))
    : []

  return (
    <Spin spinning={loading}>
      {/* 时间范围选择 */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-gray-500">LLM调用量、Token消耗和响应延迟监控</div>
        <Select
          value={days}
          onChange={setDays}
          style={{ width: 140 }}
          options={[
            { value: 7, label: '最近 7 天' },
            { value: 14, label: '最近 14 天' },
            { value: 30, label: '最近 30 天' },
            { value: 90, label: '最近 90 天' },
          ]}
        />
      </div>

      {/* 汇总统计卡片 */}
      <Row gutter={16} className="mb-4">
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总调用次数"
              value={summary?.total_calls || 0}
              prefix={<ThunderboltOutlined style={{ color: '#1677ff' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总 Token 消耗"
              value={summary?.total_tokens || 0}
              prefix={<ClockCircleOutlined style={{ color: '#722ed1' }} />}
              formatter={(val) => Number(val).toLocaleString()}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="平均延迟"
              value={summary?.avg_latency_ms || 0}
              suffix="ms"
              precision={1}
              prefix={<FieldTimeOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="成功率"
              value={(summary?.success_rate || 0) * 100}
              suffix="%"
              precision={1}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 供应商分布 */}
      {providerStats.length > 0 && (
        <Card size="small" title="供应商分布" className="mb-4">
          <div className="flex gap-6 flex-wrap">
            {providerStats.map((item) => (
              <div key={item.provider} className="flex items-center gap-2">
                <div
                  style={{
                    width: 12,
                    height: 12,
                    borderRadius: 2,
                    backgroundColor: item.color,
                  }}
                />
                <span className="text-gray-600">{item.provider}</span>
                <span className="text-gray-400">
                  {item.calls} 次 / {item.tokens.toLocaleString()} tokens
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 折线图 */}
      {trend.length > 0 ? (
        <>
          <Card size="small" title="Token 使用趋势" className="mb-4">
            <Line {...tokenLineConfig} />
          </Card>

          <Card size="small" title="延迟与调用次数趋势" className="mb-4">
            <DualAxes {...dualAxesConfig} />
          </Card>
        </>
      ) : (
        <Card className="mb-4">
          <Empty description="暂无趋势数据" />
        </Card>
      )}

      {/* 调用记录表格 */}
      <Card size="small" title="最近调用记录">
        <Table
          dataSource={logs}
          columns={logColumns}
          rowKey="id"
          size="small"
          pagination={{
            current: logsPage,
            total: logsTotal,
            pageSize: 10,
            onChange: handlePageChange,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </Spin>
  )
}
