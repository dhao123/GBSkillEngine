import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Spin, message, Space, Collapse, Modal, Select, Tabs, Empty, Timeline } from 'antd'
import { ArrowLeftOutlined, EditOutlined, PlayCircleOutlined, HistoryOutlined, SwapOutlined } from '@ant-design/icons'
import { DiffEditor } from '@monaco-editor/react'
import { skillsApi, materialParseApi } from '@/services/api'

interface Skill {
  id: number
  skill_id: string
  skill_name: string
  domain: string
  priority: number
  applicable_material_types: string[]
  dsl_content: Record<string, unknown>
  dsl_version: string
  status: string
  standard_id: number
  created_at: string
  updated_at: string
}

interface SkillVersion {
  id: number
  skill_id: number
  version: string
  dsl_content: Record<string, unknown>
  change_log: string
  is_active: boolean
  created_at: string
}

interface TestResult {
  trace_id: string
  result: {
    material_name: string
    category: Record<string, string>
    attributes: Record<string, { value: unknown; confidence: number; source: string }>
    confidence_score: number
  }
  matched_skill_id: string | null
}

export default function SkillDetail() {
  const { skillId } = useParams<{ skillId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<Skill | null>(null)
  const [loading, setLoading] = useState(true)
  const [versions, setVersions] = useState<SkillVersion[]>([])
  const [versionsLoading, setVersionsLoading] = useState(false)
  
  // 版本对比状态
  const [compareVisible, setCompareVisible] = useState(false)
  const [leftVersion, setLeftVersion] = useState<string>('')
  const [rightVersion, setRightVersion] = useState<string>('')
  
  // 测试功能状态
  const [testVisible, setTestVisible] = useState(false)
  const [testInput, setTestInput] = useState('')
  const [testLoading, setTestLoading] = useState(false)
  const [testResult, setTestResult] = useState<TestResult | null>(null)

  useEffect(() => {
    loadData()
  }, [skillId])

  const loadData = async () => {
    try {
      const res = await skillsApi.detail(skillId!)
      setData(res as Skill)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadVersions = async () => {
    if (versions.length > 0) return // 已加载
    setVersionsLoading(true)
    try {
      const res = await skillsApi.versions(skillId!)
      setVersions(res as SkillVersion[])
    } catch (error) {
      message.error('加载版本历史失败')
    } finally {
      setVersionsLoading(false)
    }
  }

  // 执行测试
  const handleTest = async () => {
    if (!testInput.trim()) {
      message.warning('请输入测试用例')
      return
    }
    setTestLoading(true)
    try {
      const res = await materialParseApi.single(testInput)
      setTestResult(res as TestResult)
    } catch (error) {
      message.error('测试执行失败')
    } finally {
      setTestLoading(false)
    }
  }

  // 获取版本DSL内容
  const getVersionContent = (version: string): string => {
    const v = versions.find(v => v.version === version)
    if (v) {
      return JSON.stringify(v.dsl_content, null, 2)
    }
    return ''
  }

  // 打开版本对比
  const openCompare = () => {
    loadVersions()
    if (versions.length >= 2) {
      setLeftVersion(versions[1]?.version || '')
      setRightVersion(versions[0]?.version || '')
    }
    setCompareVisible(true)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  if (!data) {
    return <div>Skill不存在</div>
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    testing: { color: 'blue', text: '测试中' },
    active: { color: 'green', text: '已激活' },
    deprecated: { color: 'red', text: '已停用' },
  }

  const collapseItems = [
    {
      key: 'intent',
      label: '意图识别规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.intentRecognition, null, 2)}
        </pre>
      ),
    },
    {
      key: 'extraction',
      label: '属性抽取规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.attributeExtraction, null, 2)}
        </pre>
      ),
    },
    {
      key: 'rules',
      label: '业务规则',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.rules, null, 2)}
        </pre>
      ),
    },
    {
      key: 'tables',
      label: '数据表格',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto max-h-96">
          {JSON.stringify(data.dsl_content.tables, null, 2)}
        </pre>
      ),
    },
    {
      key: 'category',
      label: '类目映射',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.categoryMapping, null, 2)}
        </pre>
      ),
    },
    {
      key: 'output',
      label: '输出结构',
      children: (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto">
          {JSON.stringify(data.dsl_content.outputStructure, null, 2)}
        </pre>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/skills')}
        >
          返回列表
        </Button>
        <Space>
          <Button 
            icon={<PlayCircleOutlined />}
            onClick={() => setTestVisible(true)}
          >
            测试
          </Button>
          <Button 
            icon={<HistoryOutlined />}
            onClick={() => {
              loadVersions()
              openCompare()
            }}
          >
            版本对比
          </Button>
          <Link to={`/skills/${skillId}/edit`}>
            <Button type="primary" icon={<EditOutlined />}>
              编辑DSL
            </Button>
          </Link>
        </Space>
      </div>

      <Card title="Skill详情">
        <Descriptions column={2}>
          <Descriptions.Item label="Skill ID">{data.skill_id}</Descriptions.Item>
          <Descriptions.Item label="名称">{data.skill_name}</Descriptions.Item>
          <Descriptions.Item label="领域">
            <Tag>
              {data.domain === 'pipe' ? '管材' : data.domain === 'fastener' ? '紧固件' : data.domain || '未分类'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[data.status]?.color || 'default'}>
              {statusMap[data.status]?.text || data.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="版本">{data.dsl_version}</Descriptions.Item>
          <Descriptions.Item label="优先级">{data.priority}</Descriptions.Item>
          <Descriptions.Item label="适用物料类型" span={2}>
            {data.applicable_material_types?.map((t) => (
              <Tag key={t}>{t}</Tag>
            ))}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(data.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(data.updated_at).toLocaleString()}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card 
        title="DSL配置"
        extra={
          <Button 
            size="small" 
            icon={<HistoryOutlined />}
            onClick={loadVersions}
            loading={versionsLoading}
          >
            查看版本历史
          </Button>
        }
      >
        <Tabs
          items={[
            {
              key: 'config',
              label: 'DSL配置',
              children: <Collapse items={collapseItems} defaultActiveKey={['intent', 'extraction']} />
            },
            {
              key: 'versions',
              label: `版本历史 ${versions.length > 0 ? `(${versions.length})` : ''}`,
              children: versionsLoading ? (
                <div className="flex justify-center py-8">
                  <Spin />
                </div>
              ) : versions.length > 0 ? (
                <div className="max-h-96 overflow-auto">
                  <Timeline
                    items={versions.map(v => ({
                      color: v.is_active ? 'green' : 'gray',
                      children: (
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">
                              版本 {v.version}
                              {v.is_active && <Tag color="green" className="ml-2">当前</Tag>}
                            </div>
                            <div className="text-gray-500 text-sm">{v.change_log}</div>
                            <div className="text-gray-400 text-xs">
                              {new Date(v.created_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                      )
                    }))}
                  />
                </div>
              ) : (
                <Empty description="暂无版本历史" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )
            }
          ]}
          onTabClick={(key) => {
            if (key === 'versions' && versions.length === 0) {
              loadVersions()
            }
          }}
        />
      </Card>

      {/* 版本对比弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <SwapOutlined />
            <span>版本对比</span>
          </div>
        }
        open={compareVisible}
        onCancel={() => setCompareVisible(false)}
        width={1200}
        footer={null}
        styles={{ body: { padding: '16px 24px' } }}
      >
        {versionsLoading ? (
          <div className="flex justify-center py-8">
            <Spin />
          </div>
        ) : versions.length < 2 ? (
          <Empty description="需要至少2个版本才能进行对比" />
        ) : (
          <>
            <div className="flex gap-4 mb-4">
              <div className="flex-1">
                <span className="text-gray-500 mr-2">旧版本:</span>
                <Select
                  value={leftVersion}
                  onChange={setLeftVersion}
                  style={{ width: 200 }}
                  options={versions.map(v => ({
                    value: v.version,
                    label: `${v.version}${v.is_active ? ' (当前)' : ''}`
                  }))}
                />
              </div>
              <div className="flex-1">
                <span className="text-gray-500 mr-2">新版本:</span>
                <Select
                  value={rightVersion}
                  onChange={setRightVersion}
                  style={{ width: 200 }}
                  options={versions.map(v => ({
                    value: v.version,
                    label: `${v.version}${v.is_active ? ' (当前)' : ''}`
                  }))}
                />
              </div>
            </div>
            
            {leftVersion && rightVersion && (
              <DiffEditor
                height="500px"
                language="json"
                original={getVersionContent(leftVersion)}
                modified={getVersionContent(rightVersion)}
                options={{
                  readOnly: true,
                  renderSideBySide: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  scrollBeyondLastLine: false,
                }}
              />
            )}
          </>
        )}
      </Modal>

      {/* 测试弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <PlayCircleOutlined />
            <span>Skill测试</span>
          </div>
        }
        open={testVisible}
        onCancel={() => {
          setTestVisible(false)
          setTestResult(null)
        }}
        width={800}
        footer={null}
      >
        <div className="space-y-4">
          <div>
            <div className="text-gray-500 mb-2">输入测试物料描述:</div>
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
                placeholder="例如: UPVC管PN1.6-DN100"
                value={testInput}
                onChange={e => setTestInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleTest()}
              />
              <Button type="primary" onClick={handleTest} loading={testLoading}>
                执行测试
              </Button>
            </div>
            <div className="mt-2 text-xs text-gray-400">
              快速示例: 
              {['UPVC管PN1.6-DN100', 'PE管DN200', '螺栓M8×25'].map(text => (
                <Button
                  key={text}
                  type="link"
                  size="small"
                  onClick={() => setTestInput(text)}
                >
                  {text}
                </Button>
              ))}
            </div>
          </div>

          {testResult && (
            <div className="border-t pt-4">
              <div className="font-medium mb-3 flex items-center justify-between">
                <span>测试结果</span>
                <Tag color={testResult.matched_skill_id === skillId ? 'green' : 'orange'}>
                  {testResult.matched_skill_id === skillId ? '匹配当前Skill' : `匹配: ${testResult.matched_skill_id || '无'}`}
                </Tag>
              </div>
              
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="物料名称" span={2}>
                  {testResult.result.material_name}
                </Descriptions.Item>
                <Descriptions.Item label="一级类目">
                  {testResult.result.category?.primaryCategory || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="二级类目">
                  {testResult.result.category?.secondaryCategory || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="三级类目">
                  {testResult.result.category?.tertiaryCategory || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="置信度">
                  <Tag color={testResult.result.confidence_score >= 0.7 ? 'green' : 'orange'}>
                    {(testResult.result.confidence_score * 100).toFixed(1)}%
                  </Tag>
                </Descriptions.Item>
              </Descriptions>

              {testResult.result.attributes && Object.keys(testResult.result.attributes).length > 0 && (
                <div className="mt-4">
                  <div className="text-gray-500 mb-2">抽取属性:</div>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(testResult.result.attributes).map(([key, attr]) => (
                      <div key={key} className="bg-gray-50 p-2 rounded text-sm flex justify-between">
                        <span className="text-gray-600">{key}:</span>
                        <span>
                          {String(attr.value)}
                          <Tag size="small" color={attr.confidence >= 0.8 ? 'green' : 'blue'} className="ml-2">
                            {attr.source}
                          </Tag>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
