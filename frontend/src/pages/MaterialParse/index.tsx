import { useState } from 'react'
import { Card, Input, Button, Spin, Descriptions, Tag, Collapse, message } from 'antd'
import { ExperimentOutlined } from '@ant-design/icons'
import { materialParseApi } from '@/services/api'

interface ParsedAttribute {
  value: unknown
  confidence: number
  source: string
}

interface ParseResult {
  material_name: string
  category: {
    primaryCategory: string
    secondaryCategory: string
    tertiaryCategory: string
    categoryId: string
  }
  attributes: Record<string, ParsedAttribute>
  standard_code: string | null
  confidence_score: number
}

interface ExecutionStep {
  engine: string
  start_time: string
  end_time: string
  duration_ms: number
  input_data: Record<string, unknown>
  output_data: Record<string, unknown>
}

interface ParseResponse {
  trace_id: string
  result: ParseResult
  execution_trace: {
    trace_id: string
    steps: ExecutionStep[]
    total_duration_ms: number
  }
  matched_skill_id: string | null
}

export default function MaterialParse() {
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ParseResponse | null>(null)

  const handleParse = async () => {
    if (!inputText.trim()) {
      message.warning('请输入物料描述')
      return
    }

    setLoading(true)
    try {
      const res = await materialParseApi.single(inputText)
      setResult(res as ParseResponse)
    } catch (error) {
      message.error('梳理失败')
    } finally {
      setLoading(false)
    }
  }

  const exampleInputs = [
    'UPVC管PN1.6-DN100',
    'PVC-U管道 DN50 PN1.0',
    'PE给水管 DN200',
    '螺栓M8×25 35CrMo 8.8级',
    '六角头螺栓 M12',
  ]

  const traceItems = result?.execution_trace.steps.map((step, index) => ({
    key: String(index),
    label: (
      <div className="flex justify-between items-center">
        <span>{step.engine}</span>
        <Tag color="blue">{step.duration_ms}ms</Tag>
      </div>
    ),
    children: (
      <div className="space-y-2">
        <div>
          <div className="text-gray-500 text-sm mb-1">输入:</div>
          <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">
            {JSON.stringify(step.input_data, null, 2)}
          </pre>
        </div>
        <div>
          <div className="text-gray-500 text-sm mb-1">输出:</div>
          <pre className="bg-gray-50 p-2 rounded text-xs overflow-auto">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </div>
      </div>
    ),
  }))

  return (
    <div className="space-y-4">
      {/* 输入区域 */}
      <Card title="物料梳理">
        <div className="space-y-4">
          <Input.TextArea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="请输入物料描述，例如: UPVC管PN1.6-DN100"
            rows={3}
            style={{ fontSize: 16 }}
          />
          <div className="flex justify-between items-center">
            <div className="text-gray-400 text-sm">
              示例输入:
              {exampleInputs.map((text) => (
                <Button
                  key={text}
                  type="link"
                  size="small"
                  onClick={() => setInputText(text)}
                >
                  {text}
                </Button>
              ))}
            </div>
            <Button
              type="primary"
              icon={<ExperimentOutlined />}
              onClick={handleParse}
              loading={loading}
              size="large"
            >
              开始梳理
            </Button>
          </div>
        </div>
      </Card>

      {/* 结果区域 */}
      {loading && (
        <Card>
          <div className="flex justify-center items-center h-32">
            <Spin size="large" tip="正在梳理..." />
          </div>
        </Card>
      )}

      {result && !loading && (
        <>
          {/* 结构化结果 */}
          <Card
            title={
              <div className="flex justify-between items-center">
                <span>梳理结果</span>
                <Tag color={result.result.confidence_score >= 0.7 ? 'green' : 'orange'}>
                  置信度: {(result.result.confidence_score * 100).toFixed(1)}%
                </Tag>
              </div>
            }
          >
            <Descriptions column={2} bordered>
              <Descriptions.Item label="物料名称" span={2}>
                <span className="text-lg font-medium">{result.result.material_name}</span>
              </Descriptions.Item>
              <Descriptions.Item label="一级类目">
                {result.result.category.primaryCategory}
              </Descriptions.Item>
              <Descriptions.Item label="二级类目">
                {result.result.category.secondaryCategory}
              </Descriptions.Item>
              <Descriptions.Item label="三级类目">
                {result.result.category.tertiaryCategory}
              </Descriptions.Item>
              <Descriptions.Item label="适用标准">
                {result.result.standard_code || '-'}
              </Descriptions.Item>
              {Object.entries(result.result.attributes).map(([key, attr]) => (
                <Descriptions.Item key={key} label={key}>
                  <div className="flex items-center gap-2">
                    <span>{String(attr.value)}</span>
                    <Tag color={attr.confidence >= 0.8 ? 'green' : attr.confidence >= 0.5 ? 'blue' : 'orange'}>
                      {attr.source}
                    </Tag>
                    <span className="text-gray-400 text-sm">
                      ({(attr.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>

          {/* 执行Trace */}
          <Card
            title={
              <div className="flex justify-between items-center">
                <span>执行Trace</span>
                <div className="text-sm text-gray-500">
                  Trace ID: {result.trace_id} | 
                  匹配Skill: {result.matched_skill_id || '无'} | 
                  总耗时: {result.execution_trace.total_duration_ms}ms
                </div>
              </div>
            }
          >
            <Collapse items={traceItems} />
          </Card>
        </>
      )}
    </div>
  )
}
