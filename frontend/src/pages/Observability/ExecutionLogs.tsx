import { useEffect, useState } from 'react'
import { Card, Tag, Input, Select, message, Modal, Collapse, Descriptions } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import BaseTable from '@/components/BaseTable'
import { observabilityApi } from '@/services/api'
import dayjs from 'dayjs'

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

export default function ExecutionLogs() {
  const [data, setData] = useState<ExecutionLog[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [status, setStatus] = useState<string | undefined>()
  const [skillId, setSkillId] = useState('')
  const [detailVisible, setDetailVisible] = useState(false)
  const [traceDetail, setTraceDetail] = useState<TraceDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [page, pageSize, status, skillId])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await observabilityApi.executionLogs({
        page,
        page_size: pageSize,
        status,
        skill_id: skillId || undefined,
      }) as { items: ExecutionLog[]; total: number }
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

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
      <Card>
        <div className="flex gap-4 mb-4">
          <Input
            placeholder="搜索Skill ID"
            prefix={<SearchOutlined />}
            value={skillId}
            onChange={(e) => setSkillId(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            value={status}
            onChange={setStatus}
            allowClear
            options={[
              { value: 'success', label: '成功' },
              { value: 'failed', label: '失败' },
            ]}
          />
        </div>

        <BaseTable
          columns={columns}
          dataSource={data}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

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
