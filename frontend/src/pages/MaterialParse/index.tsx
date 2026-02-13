import { useState, useCallback } from 'react'
import { Card, Input, Button, Spin, Descriptions, Tag, Collapse, message, Tabs, Table, Space, Modal, Form, InputNumber, Slider, Upload, Drawer, Empty } from 'antd'
import { 
  ExperimentOutlined, 
  DownloadOutlined, 
  UploadOutlined, 
  HistoryOutlined,
  EditOutlined,
  CheckOutlined,
  SettingOutlined,
  DeleteOutlined,
  PlusOutlined
} from '@ant-design/icons'
import { materialParseApi, observabilityApi } from '@/services/api'
import * as XLSX from 'xlsx'
import dayjs from 'dayjs'

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

interface BatchItem {
  id: number
  inputText: string
  status: 'pending' | 'processing' | 'success' | 'failed' | 'reviewed'
  result?: ParseResponse
  editedResult?: ParseResult
  error?: string
}

interface HistoryLog {
  id: number
  trace_id: string
  input_text: string
  executed_skill_id: string | null
  output_result: ParseResult | null
  confidence_score: number | null
  execution_time_ms: number | null
  status: string
  created_at: string
}

// 置信度阈值配置
const DEFAULT_CONFIDENCE_THRESHOLD = 0.7

export default function MaterialParse() {
  // 单条梳理状态
  const [inputText, setInputText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ParseResponse | null>(null)
  
  // 批量梳理状态
  const [batchItems, setBatchItems] = useState<BatchItem[]>([])
  const [batchProcessing, setBatchProcessing] = useState(false)
  
  // 配置状态
  const [confidenceThreshold, setConfidenceThreshold] = useState(DEFAULT_CONFIDENCE_THRESHOLD)
  const [settingsVisible, setSettingsVisible] = useState(false)
  
  // 编辑状态
  const [editingItem, setEditingItem] = useState<BatchItem | null>(null)
  const [editDrawerVisible, setEditDrawerVisible] = useState(false)
  const [editForm] = Form.useForm()
  
  // 历史记录状态
  const [historyVisible, setHistoryVisible] = useState(false)
  const [historyData, setHistoryData] = useState<HistoryLog[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyPage, setHistoryPage] = useState(1)

  // 单条梳理
  const handleParse = async () => {
    if (!inputText.trim()) {
      message.warning('请输入物料描述')
      return
    }

    setLoading(true)
    try {
      const res = await materialParseApi.single(inputText)
      setResult(res as ParseResponse)
      
      // 检查置信度，给出提示
      const confidence = (res as ParseResponse).result.confidence_score
      if (confidence < confidenceThreshold) {
        message.warning(`置信度 ${(confidence * 100).toFixed(1)}% 低于阈值 ${(confidenceThreshold * 100).toFixed(0)}%，建议人工审核`)
      }
    } catch (error) {
      message.error('梳理失败')
    } finally {
      setLoading(false)
    }
  }

  // 批量梳理
  const handleBatchParse = async () => {
    if (batchItems.length === 0) {
      message.warning('请先添加待梳理的物料')
      return
    }

    setBatchProcessing(true)
    const updatedItems = [...batchItems]

    for (let i = 0; i < updatedItems.length; i++) {
      if (updatedItems[i].status === 'reviewed') continue // 跳过已审核的
      
      updatedItems[i].status = 'processing'
      setBatchItems([...updatedItems])

      try {
        const res = await materialParseApi.single(updatedItems[i].inputText)
        updatedItems[i].result = res as ParseResponse
        updatedItems[i].status = 'success'
        
        // 低置信度标记需要审核
        const confidence = (res as ParseResponse).result.confidence_score
        if (confidence < confidenceThreshold) {
          updatedItems[i].status = 'success' // 保持成功状态，但会显示警告
        }
      } catch (e) {
        updatedItems[i].status = 'failed'
        updatedItems[i].error = (e as Error).message
      }

      setBatchItems([...updatedItems])
    }

    setBatchProcessing(false)
    message.success('批量梳理完成')
  }

  // 添加批量项
  const addBatchItem = (text: string) => {
    if (!text.trim()) return
    setBatchItems(prev => [...prev, {
      id: Date.now(),
      inputText: text.trim(),
      status: 'pending'
    }])
  }

  // 从文本批量添加
  const handleBatchAdd = () => {
    Modal.confirm({
      title: '批量添加物料',
      icon: <PlusOutlined />,
      width: 500,
      content: (
        <div>
          <p className="text-gray-500 mb-2">请输入物料描述，每行一个:</p>
          <Input.TextArea 
            id="batchInput"
            rows={8} 
            placeholder="UPVC管PN1.6-DN100&#10;PE管DN200&#10;螺栓M8×25"
          />
        </div>
      ),
      onOk: () => {
        const textarea = document.getElementById('batchInput') as HTMLTextAreaElement
        const lines = textarea.value.split('\n').filter(line => line.trim())
        lines.forEach(line => addBatchItem(line))
        message.success(`已添加 ${lines.length} 条物料`)
      }
    })
  }

  // 导出Excel
  const handleExportExcel = () => {
    const exportData = batchItems
      .filter(item => item.result || item.editedResult)
      .map(item => {
        const r = item.editedResult || item.result?.result
        if (!r) return null
        return {
          '输入描述': item.inputText,
          '物料名称': r.material_name,
          '一级类目': r.category.primaryCategory,
          '二级类目': r.category.secondaryCategory,
          '三级类目': r.category.tertiaryCategory,
          '适用标准': r.standard_code || '',
          '置信度': r.confidence_score,
          '状态': item.status === 'reviewed' ? '已审核' : '待审核',
          ...Object.fromEntries(
            Object.entries(r.attributes || {}).map(([k, v]) => [k, v.value])
          )
        }
      })
      .filter(Boolean)

    if (exportData.length === 0) {
      message.warning('没有可导出的数据')
      return
    }

    const ws = XLSX.utils.json_to_sheet(exportData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '物料梳理结果')
    XLSX.writeFile(wb, `物料梳理结果_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`)
    message.success('导出成功')
  }

  // 导出CSV
  const handleExportCSV = () => {
    const exportData = batchItems
      .filter(item => item.result || item.editedResult)
      .map(item => {
        const r = item.editedResult || item.result?.result
        if (!r) return null
        return {
          '输入描述': item.inputText,
          '物料名称': r.material_name,
          '一级类目': r.category.primaryCategory,
          '二级类目': r.category.secondaryCategory,
          '三级类目': r.category.tertiaryCategory,
          '适用标准': r.standard_code || '',
          '置信度': r.confidence_score,
        }
      })
      .filter(Boolean)

    if (exportData.length === 0) {
      message.warning('没有可导出的数据')
      return
    }

    const ws = XLSX.utils.json_to_sheet(exportData)
    const csv = XLSX.utils.sheet_to_csv(ws)
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `物料梳理结果_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    link.click()
    URL.revokeObjectURL(url)
    message.success('导出成功')
  }

  // 打开编辑抽屉
  const openEditDrawer = (item: BatchItem) => {
    setEditingItem(item)
    const r = item.editedResult || item.result?.result
    if (r) {
      editForm.setFieldsValue({
        material_name: r.material_name,
        primaryCategory: r.category.primaryCategory,
        secondaryCategory: r.category.secondaryCategory,
        tertiaryCategory: r.category.tertiaryCategory,
        standard_code: r.standard_code,
        ...Object.fromEntries(
          Object.entries(r.attributes || {}).map(([k, v]) => [`attr_${k}`, v.value])
        )
      })
    }
    setEditDrawerVisible(true)
  }

  // 保存编辑
  const handleSaveEdit = () => {
    editForm.validateFields().then(values => {
      if (!editingItem) return

      const editedResult: ParseResult = {
        material_name: values.material_name,
        category: {
          primaryCategory: values.primaryCategory,
          secondaryCategory: values.secondaryCategory,
          tertiaryCategory: values.tertiaryCategory,
          categoryId: editingItem.result?.result.category.categoryId || ''
        },
        standard_code: values.standard_code,
        attributes: Object.fromEntries(
          Object.entries(editingItem.result?.result.attributes || {}).map(([k, v]) => [
            k,
            { ...v as ParsedAttribute, value: values[`attr_${k}`] ?? (v as ParsedAttribute).value }
          ])
        ),
        confidence_score: 1.0 // 人工审核后置信度设为1
      }

      setBatchItems(prev => prev.map(item => 
        item.id === editingItem.id 
          ? { ...item, editedResult, status: 'reviewed' as const }
          : item
      ))

      setEditDrawerVisible(false)
      message.success('保存成功')
    })
  }

  // 加载历史记录
  const loadHistory = useCallback(async (page: number = 1) => {
    setHistoryLoading(true)
    try {
      const res = await observabilityApi.executionLogs({ page, page_size: 10 }) as {
        items: HistoryLog[]
        total: number
      }
      setHistoryData(res.items)
      setHistoryTotal(res.total)
      setHistoryPage(page)
    } catch (error) {
      message.error('加载历史记录失败')
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  // 从历史重新梳理
  const reparseFromHistory = (text: string) => {
    setInputText(text)
    setHistoryVisible(false)
    message.info('已填入输入框，点击"开始梳理"执行')
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

  // 批量表格列
  const batchColumns = [
    { title: '序号', width: 60, render: (_: unknown, __: unknown, index: number) => index + 1 },
    { title: '输入描述', dataIndex: 'inputText', ellipsis: true },
    { 
      title: '物料名称', 
      width: 150,
      render: (_: unknown, record: BatchItem) => 
        record.editedResult?.material_name || record.result?.result.material_name || '-'
    },
    { 
      title: '置信度', 
      width: 100,
      render: (_: unknown, record: BatchItem) => {
        const score = record.editedResult?.confidence_score || record.result?.result.confidence_score
        if (score === undefined) return '-'
        const isLow = score < confidenceThreshold
        return (
          <Tag color={record.status === 'reviewed' ? 'green' : isLow ? 'orange' : 'blue'}>
            {(score * 100).toFixed(1)}%
          </Tag>
        )
      }
    },
    {
      title: '状态',
      width: 100,
      render: (_: unknown, record: BatchItem) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          pending: { color: 'default', text: '待处理' },
          processing: { color: 'processing', text: '处理中' },
          success: { color: 'blue', text: '已完成' },
          failed: { color: 'red', text: '失败' },
          reviewed: { color: 'green', text: '已审核' },
        }
        return <Tag color={statusMap[record.status]?.color}>{statusMap[record.status]?.text}</Tag>
      }
    },
    {
      title: '操作',
      width: 120,
      render: (_: unknown, record: BatchItem) => (
        <Space size="small">
          {record.result && (
            <Button 
              type="link" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => openEditDrawer(record)}
            >
              {record.status === 'reviewed' ? '查看' : '审核'}
            </Button>
          )}
          <Button 
            type="link" 
            size="small" 
            danger
            icon={<DeleteOutlined />}
            onClick={() => setBatchItems(prev => prev.filter(i => i.id !== record.id))}
          />
        </Space>
      )
    },
  ]

  return (
    <div className="space-y-4">
      <Tabs
        items={[
          {
            key: 'single',
            label: '单条梳理',
            children: (
              <div className="space-y-4">
                {/* 输入区域 */}
                <Card 
                  title="物料梳理"
                  extra={
                    <Space>
                      <Button 
                        icon={<SettingOutlined />} 
                        onClick={() => setSettingsVisible(true)}
                        size="small"
                      >
                        设置
                      </Button>
                      <Button 
                        icon={<HistoryOutlined />}
                        onClick={() => {
                          setHistoryVisible(true)
                          loadHistory()
                        }}
                        size="small"
                      >
                        历史记录
                      </Button>
                    </Space>
                  }
                >
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
                          <Tag color={result.result.confidence_score >= confidenceThreshold ? 'green' : 'orange'}>
                            置信度: {(result.result.confidence_score * 100).toFixed(1)}%
                            {result.result.confidence_score < confidenceThreshold && ' (需审核)'}
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
          },
          {
            key: 'batch',
            label: `批量梳理 ${batchItems.length > 0 ? `(${batchItems.length})` : ''}`,
            children: (
              <div className="space-y-4">
                <Card
                  title="批量物料梳理"
                  extra={
                    <Space>
                      <span className="text-gray-500 text-sm">
                        置信度阈值: {(confidenceThreshold * 100).toFixed(0)}%
                      </span>
                      <Button icon={<SettingOutlined />} onClick={() => setSettingsVisible(true)} size="small">
                        设置
                      </Button>
                    </Space>
                  }
                >
                  <div className="space-y-4">
                    {/* 操作栏 */}
                    <div className="flex justify-between items-center">
                      <Space>
                        <Input
                          placeholder="输入物料描述后回车添加"
                          style={{ width: 300 }}
                          onPressEnter={(e) => {
                            addBatchItem((e.target as HTMLInputElement).value)
                            ;(e.target as HTMLInputElement).value = ''
                          }}
                        />
                        <Button icon={<PlusOutlined />} onClick={handleBatchAdd}>
                          批量添加
                        </Button>
                        <Upload
                          accept=".txt,.csv"
                          showUploadList={false}
                          beforeUpload={(file) => {
                            const reader = new FileReader()
                            reader.onload = (e) => {
                              const text = e.target?.result as string
                              const lines = text.split('\n').filter(line => line.trim())
                              lines.forEach(line => addBatchItem(line.split(',')[0])) // CSV取第一列
                              message.success(`已添加 ${lines.length} 条物料`)
                            }
                            reader.readAsText(file)
                            return false
                          }}
                        >
                          <Button icon={<UploadOutlined />}>导入文件</Button>
                        </Upload>
                      </Space>
                      <Space>
                        <Button 
                          icon={<DownloadOutlined />} 
                          onClick={handleExportExcel}
                          disabled={batchItems.filter(i => i.result).length === 0}
                        >
                          导出Excel
                        </Button>
                        <Button 
                          icon={<DownloadOutlined />} 
                          onClick={handleExportCSV}
                          disabled={batchItems.filter(i => i.result).length === 0}
                        >
                          导出CSV
                        </Button>
                        <Button 
                          type="primary"
                          icon={<ExperimentOutlined />}
                          onClick={handleBatchParse}
                          loading={batchProcessing}
                          disabled={batchItems.length === 0}
                        >
                          开始批量梳理
                        </Button>
                      </Space>
                    </div>

                    {/* 批量列表 */}
                    <Table
                      columns={batchColumns}
                      dataSource={batchItems}
                      rowKey="id"
                      pagination={false}
                      scroll={{ y: 400 }}
                      locale={{
                        emptyText: <Empty description="暂无数据，请添加待梳理的物料" />
                      }}
                    />

                    {/* 统计信息 */}
                    {batchItems.length > 0 && (
                      <div className="flex gap-4 text-sm text-gray-500">
                        <span>总计: {batchItems.length}</span>
                        <span>待处理: {batchItems.filter(i => i.status === 'pending').length}</span>
                        <span>已完成: {batchItems.filter(i => i.status === 'success').length}</span>
                        <span>已审核: {batchItems.filter(i => i.status === 'reviewed').length}</span>
                        <span>失败: {batchItems.filter(i => i.status === 'failed').length}</span>
                        <span className="text-orange-500">
                          需审核: {batchItems.filter(i => i.result && i.result.result.confidence_score < confidenceThreshold && i.status !== 'reviewed').length}
                        </span>
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )
          }
        ]}
      />

      {/* 设置弹窗 */}
      <Modal
        title={<><SettingOutlined /> 梳理设置</>}
        open={settingsVisible}
        onCancel={() => setSettingsVisible(false)}
        onOk={() => setSettingsVisible(false)}
      >
        <div className="py-4">
          <div className="mb-4">
            <div className="text-gray-600 mb-2">置信度阈值</div>
            <div className="text-gray-400 text-sm mb-2">
              低于此阈值的结果会标记为"需审核"
            </div>
            <div className="flex items-center gap-4">
              <Slider
                value={confidenceThreshold * 100}
                onChange={(v) => setConfidenceThreshold(v / 100)}
                min={0}
                max={100}
                style={{ flex: 1 }}
              />
              <InputNumber
                value={Math.round(confidenceThreshold * 100)}
                onChange={(v) => setConfidenceThreshold((v || 70) / 100)}
                min={0}
                max={100}
                formatter={(v) => `${v}%`}
                parser={(v) => Number(v?.replace('%', '') || 70)}
                style={{ width: 80 }}
              />
            </div>
          </div>
        </div>
      </Modal>

      {/* 编辑抽屉 */}
      <Drawer
        title={<><EditOutlined /> 人工审核修正</>}
        open={editDrawerVisible}
        onClose={() => setEditDrawerVisible(false)}
        width={500}
        footer={
          <Space>
            <Button onClick={() => setEditDrawerVisible(false)}>取消</Button>
            <Button type="primary" icon={<CheckOutlined />} onClick={handleSaveEdit}>
              确认保存
            </Button>
          </Space>
        }
      >
        {editingItem && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-gray-500 text-sm">原始输入:</div>
              <div className="font-medium">{editingItem.inputText}</div>
            </div>
            
            <Form form={editForm} layout="vertical">
              <Form.Item name="material_name" label="物料名称" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="primaryCategory" label="一级类目">
                <Input />
              </Form.Item>
              <Form.Item name="secondaryCategory" label="二级类目">
                <Input />
              </Form.Item>
              <Form.Item name="tertiaryCategory" label="三级类目">
                <Input />
              </Form.Item>
              <Form.Item name="standard_code" label="适用标准">
                <Input />
              </Form.Item>
              
              {editingItem.result?.result.attributes && Object.keys(editingItem.result.result.attributes).length > 0 && (
                <>
                  <div className="text-gray-500 mb-2">属性值:</div>
                  {Object.entries(editingItem.result.result.attributes).map(([key, attr]) => (
                    <Form.Item 
                      key={key} 
                      name={`attr_${key}`} 
                      label={
                        <span>
                          {key}
                          <Tag size="small" className="ml-2">{attr.source}</Tag>
                        </span>
                      }
                    >
                      <Input />
                    </Form.Item>
                  ))}
                </>
              )}
            </Form>
          </div>
        )}
      </Drawer>

      {/* 历史记录抽屉 */}
      <Drawer
        title={<><HistoryOutlined /> 梳理历史记录</>}
        open={historyVisible}
        onClose={() => setHistoryVisible(false)}
        width={700}
      >
        <Table
          columns={[
            { 
              title: '时间', 
              dataIndex: 'created_at', 
              width: 160,
              render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm:ss')
            },
            { title: '输入', dataIndex: 'input_text', ellipsis: true },
            { 
              title: '匹配Skill', 
              dataIndex: 'executed_skill_id', 
              width: 150,
              render: (id: string) => id || '-'
            },
            { 
              title: '置信度', 
              dataIndex: 'confidence_score', 
              width: 80,
              render: (s: number) => s ? `${(s * 100).toFixed(0)}%` : '-'
            },
            {
              title: '操作',
              width: 80,
              render: (_: unknown, record: HistoryLog) => (
                <Button type="link" size="small" onClick={() => reparseFromHistory(record.input_text)}>
                  重新梳理
                </Button>
              )
            }
          ]}
          dataSource={historyData}
          loading={historyLoading}
          rowKey="id"
          pagination={{
            current: historyPage,
            total: historyTotal,
            pageSize: 10,
            onChange: loadHistory
          }}
          size="small"
        />
      </Drawer>
    </div>
  )
}
