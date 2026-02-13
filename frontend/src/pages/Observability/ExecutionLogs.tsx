import { useEffect, useState, useCallback } from 'react'
import { Card, Tag, Input, Select, message, Modal, Collapse, Descriptions, DatePicker, Button, Space, Row, Col, Statistic } from 'antd'
import { 
  SearchOutlined, 
  DownloadOutlined, 
  ReloadOutlined,
  LineChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons'
import BaseTable from '@/components/BaseTable'
import { observabilityApi } from '@/services/api'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import * as XLSX from 'xlsx'

const { RangePicker } = DatePicker

interface ExecutionLog {
  id: number
  trace_id: string
  input_text: string
  executed_skill_id: string | null
  output_result: Record<string, unknown> | null
  confidence_score: number | null
  execution_time_ms: number | null
  status: string
  created_at: string
}

interface TraceDetail {
  trace_id: string
  input_text: string
  matched_skills: string[]
  executed_skill_id: string | null
  execution_trace: {
    steps: Array<{
      engine: string
      duration_ms: number
      input_data: Record<string, unknown>
      output_data: Record<string, unknown>
    }>
  }
  output_result: Record<string, unknown> | null
  confidence_score: number | null
  execution_time_ms: number | null
  status: string
  error_message: string | null
  created_at: string
}

interface Metrics {
  total_executions: number
  success_count: number
  success_rate: number
  avg_confidence: number
  avg_execution_time_ms: number
}

// 简单的趋势图组件（使用CSS绘制）
function TrendChart({ data, title }: { data: { date: string; count: number; successRate: number }[]; title: string }) {
  if (data.length === 0) return null
  
  const maxCount = Math.max(...data.map(d => d.count), 1)
  
  return (
    <div className="mt-4">
      <div className="text-gray-500 text-sm mb-2">{title}</div>
      <div className="flex items-end gap-1 h-24 border-b border-gray-200">
        {data.map((item, idx) => (
          <div key={idx} className="flex-1 flex flex-col items-center">
            <div 
              className="w-full bg-blue-500 rounded-t transition-all"
              style={{ 
                height: `${(item.count / maxCount) * 100}%`,
                minHeight: item.count > 0 ? 4 : 0
              }}
              title={`${item.date}: ${item.count}次`}
            />
          </div>
        ))}
      </div>
      <div className="flex gap-1 text-xs text-gray-400 mt-1">
        {data.map((item, idx) => (
          <div key={idx} className="flex-1 text-center truncate" title={item.date}>
            {dayjs(item.date).format('MM/DD')}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ExecutionLogs() {
  const [data, setData] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [status, setStatus] = useState<string | undefined>()
  const [skillId, setSkillId] = useState('')
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  const [traceDetail, setTraceDetail] = useState<TraceDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [trendData, setTrendData] = useState<{ date: string; count: number; successRate: number }[]>([])
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    loadData()
    loadMetrics()
  }, [page, pageSize, status, skillId, dateRange])

  const loadData = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = {
        page,
        page_size: pageSize,
        status,
        skill_id: skillId || undefined,
      }
      
      if (dateRange && dateRange[0] && dateRange[1]) {
        params.start_time = dateRange[0].startOf('day').toISOString()
        params.end_time = dateRange[1].endOf('day').toISOString()
      }
      
      const res = await observabilityApi.executionLogs(params) as { items: ExecutionLog[]; total: number }
      setData(res.items || [])
      setTotal(res.total || 0)
      
      // 简单计算趋势数据（从返回数据中计算最近7天）
      calculateTrendData(res.items)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      const res = await observabilityApi.metrics()
      setMetrics(res as Metrics)
    } catch (error) {
      console.error('加载指标失败')
    }
  }

  // 计算趋势数据
  const calculateTrendData = useCallback((logs: ExecutionLog[]) => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = dayjs().subtract(6 - i, 'day').format('YYYY-MM-DD')
      return { date, count: 0, successCount: 0, successRate: 0 }
    })

    logs.forEach(log => {
      const logDate = dayjs(log.created_at).format('YYYY-MM-DD')
      const dayData = last7Days.find(d => d.date === logDate)
      if (dayData) {
        dayData.count++
        if (log.status === 'success') {
          dayData.successCount++
        }
      }
    })

    last7Days.forEach(d => {
      d.successRate = d.count > 0 ? d.successCount / d.count : 0
    })

    setTrendData(last7Days)
  }, [])

  const showDetail = async (traceId: string) => {
    setDetailLoading(true)
    setDetailVisible(true)
    try {
      const res = await observabilityApi.traceDetail(traceId)
      setTraceDetail(res as TraceDetail)
    } catch (error) {
      message.error('加载详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  // 导出Excel
  const handleExportExcel = async () => {
    setExporting(true)
    try {
      // 获取所有数据（最多1000条）
      const res = await observabilityApi.executionLogs({
        page: 1,
        page_size: 1000,
        status,
        skill_id: skillId || undefined,
        start_time: dateRange?.[0]?.startOf('day').toISOString(),
        end_time: dateRange?.[1]?.endOf('day').toISOString(),
      }) as { items: ExecutionLog[] }

      const exportData = res.items.map(item => ({
        'Trace ID': item.trace_id,
        '输入': item.input_text,
        '匹配Skill': item.executed_skill_id || '',
        '置信度': item.confidence_score ? `${(item.confidence_score * 100).toFixed(1)}%` : '',
        '耗时(ms)': item.execution_time_ms || '',
        '状态': item.status === 'success' ? '成功' : '失败',
        '执行时间': dayjs(item.created_at).format('YYYY-MM-DD HH:mm:ss'),
      }))

      const ws = XLSX.utils.json_to_sheet(exportData)
      const wb = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(wb, ws, '执行日志')
      XLSX.writeFile(wb, `执行日志_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
    } finally {
      setExporting(false)
    }
  }

  // 导出CSV
  const handleExportCSV = async () => {
    setExporting(true)
    try {
      const res = await observabilityApi.executionLogs({
        page: 1,
        page_size: 1000,
        status,
        skill_id: skillId || undefined,
        start_time: dateRange?.[0]?.startOf('day').toISOString(),
        end_time: dateRange?.[1]?.endOf('day').toISOString(),
      }) as { items: ExecutionLog[] }

      const exportData = res.items.map(item => ({
        'Trace ID': item.trace_id,
        '输入': item.input_text,
        '匹配Skill': item.executed_skill_id || '',
        '置信度': item.confidence_score || '',
        '耗时(ms)': item.execution_time_ms || '',
        '状态': item.status,
        '执行时间': item.created_at,
      }))

      const ws = XLSX.utils.json_to_sheet(exportData)
      const csv = XLSX.utils.sheet_to_csv(ws)
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `执行日志_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
      link.click()
      URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
    } finally {
      setExporting(false)
    }
  }

  // 快捷日期选择
  const handleQuickDate = (days: number) => {
    if (days === 0) {
      setDateRange(null)
    } else {
      setDateRange([dayjs().subtract(days - 1, 'day'), dayjs()])
    }
    setPage(1)
  }

  const columns = [
    {
      title: 'Trace ID',
      dataIndex: 'trace_id',
      key: 'trace_id',
      width: 280,
      render: (id: string) => (
        <a onClick={() => showDetail(id)}>{id}</a>
      ),
    },
    {
      title: '输入',
      dataIndex: 'input_text',
      key: 'input_text',
      width: 200,
      ellipsis: true,
    },
    {
      title: '匹配Skill',
      dataIndex: 'executed_skill_id',
      key: 'executed_skill_id',
      width: 180,
      render: (id: string | null) => id || <span className="text-gray-400">-</span>,
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      width: 100,
      render: (score: number | null) =>
        score !== null ? (
          <Tag color={score >= 0.7 ? 'green' : score >= 0.5 ? 'blue' : 'orange'}>
            {(score * 100).toFixed(1)}%
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: '耗时',
      dataIndex: 'execution_time_ms',
      key: 'execution_time_ms',
      width: 80,
      render: (time: number | null) => (time !== null ? `${time}ms` : '-'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : status === 'failed' ? 'red' : 'orange'}>
          {status === 'success' ? '成功' : status === 'failed' ? '失败' : status}
        </Tag>
      ),
    },
    {
      title: '执行时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm:ss'),
    },
  ]

  const traceItems = traceDetail?.execution_trace?.steps?.map((step, index) => ({
    key: String(index),
    label: (
      <div className="flex justify-between items-center">
        <span>{step.engine}</span>
        <Tag color="blue">{step.duration_ms}ms</Tag>
      </div>
    ),
    children: (
      <div className="space-y-2 text-xs">
        <div>
          <div className="text-gray-500 mb-1">输入:</div>
          <pre className="bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(step.input_data, null, 2)}
          </pre>
        </div>
        <div>
          <div className="text-gray-500 mb-1">输出:</div>
          <pre className="bg-gray-50 p-2 rounded overflow-auto">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </div>
      </div>
    ),
  }))

  return (
    <div className="space-y-4">
      {/* 统计卡片 */}
      <Row gutter={16}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="总执行次数"
              value={metrics?.total_executions || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#3462FE' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="成功次数"
              value={metrics?.success_count || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="成功率"
              value={((metrics?.success_rate || 0) * 100).toFixed(1)}
              suffix="%"
              prefix={<LineChartOutlined />}
              valueStyle={{ color: metrics?.success_rate && metrics.success_rate >= 0.9 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="平均耗时"
              value={metrics?.avg_execution_time_ms?.toFixed(0) || 0}
              suffix="ms"
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#666' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 趋势图表 */}
      <Card size="small" title={<><LineChartOutlined /> 执行趋势 (最近7天)</>}>
        <Row gutter={16}>
          <Col span={12}>
            <TrendChart data={trendData} title="执行次数" />
          </Col>
          <Col span={12}>
            <div className="mt-4">
              <div className="text-gray-500 text-sm mb-2">每日统计</div>
              <div className="grid grid-cols-7 gap-2 text-xs">
                {trendData.map((item, idx) => (
                  <div key={idx} className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-gray-400">{dayjs(item.date).format('MM/DD')}</div>
                    <div className="font-medium text-blue-600">{item.count}次</div>
                    <div className="text-green-500">{(item.successRate * 100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 日志列表 */}
      <Card>
        {/* 筛选工具栏 */}
        <div className="flex flex-wrap gap-4 mb-4">
          <Input
            placeholder="搜索Skill ID"
            prefix={<SearchOutlined />}
            value={skillId}
            onChange={(e) => {
              setSkillId(e.target.value)
              setPage(1)
            }}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            value={status}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
            allowClear
            options={[
              { value: 'success', label: '成功' },
              { value: 'failed', label: '失败' },
            ]}
          />
          <RangePicker
            value={dateRange}
            onChange={(dates) => {
              setDateRange(dates as [Dayjs | null, Dayjs | null] | null)
              setPage(1)
            }}
            placeholder={['开始日期', '结束日期']}
          />
          <Space>
            <Button size="small" onClick={() => handleQuickDate(1)}>今天</Button>
            <Button size="small" onClick={() => handleQuickDate(7)}>近7天</Button>
            <Button size="small" onClick={() => handleQuickDate(30)}>近30天</Button>
            <Button size="small" onClick={() => handleQuickDate(0)}>全部</Button>
          </Space>
          
          <div className="flex-1" />
          
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => {
                loadData()
                loadMetrics()
              }}
            >
              刷新
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={handleExportExcel}
              loading={exporting}
            >
              导出Excel
            </Button>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={handleExportCSV}
              loading={exporting}
            >
              导出CSV
            </Button>
          </Space>
        </div>

        {/* 筛选结果提示 */}
        {(status || skillId || dateRange) && (
          <div className="mb-4 text-sm text-gray-500">
            筛选条件: 
            {status && <Tag className="ml-2">状态: {status === 'success' ? '成功' : '失败'}</Tag>}
            {skillId && <Tag className="ml-2">Skill: {skillId}</Tag>}
            {dateRange && dateRange[0] && dateRange[1] && (
              <Tag className="ml-2">
                时间: {dateRange[0].format('YYYY-MM-DD')} ~ {dateRange[1].format('YYYY-MM-DD')}
              </Tag>
            )}
            <Button 
              type="link" 
              size="small"
              onClick={() => {
                setStatus(undefined)
                setSkillId('')
                setDateRange(null)
                setPage(1)
              }}
            >
              清除筛选
            </Button>
          </div>
        )}

        <BaseTable
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (t) => `共 ${t} 条记录`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      {/* Trace详情弹窗 */}
      <Modal
        title="执行Trace详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {detailLoading ? (
          <div className="text-center py-8">加载中...</div>
        ) : traceDetail ? (
          <div className="space-y-4">
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Trace ID">{traceDetail.trace_id}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={traceDetail.status === 'success' ? 'green' : 'red'}>
                  {traceDetail.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="输入" span={2}>
                {traceDetail.input_text}
              </Descriptions.Item>
              <Descriptions.Item label="匹配Skill">
                {traceDetail.executed_skill_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                {traceDetail.confidence_score !== null
                  ? `${(traceDetail.confidence_score * 100).toFixed(1)}%`
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="耗时">
                {traceDetail.execution_time_ms}ms
              </Descriptions.Item>
              <Descriptions.Item label="执行时间">
                {dayjs(traceDetail.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            <div>
              <div className="font-medium mb-2">执行步骤</div>
              <Collapse items={traceItems} />
            </div>

            {traceDetail.output_result && (
              <div>
                <div className="font-medium mb-2">输出结果</div>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-auto max-h-60">
                  {JSON.stringify(traceDetail.output_result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ) : null}
      </Modal>
    </div>
  )
}
