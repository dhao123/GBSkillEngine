import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Button, Spin, message, Space, Select, Tooltip, Modal, Alert } from 'antd'
import { 
  ArrowLeftOutlined, 
  SaveOutlined, 
  FormatPainterOutlined,
  ExpandOutlined,
  CompressOutlined,
  CopyOutlined,
  UndoOutlined,
  RedoOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons'
import Editor, { OnMount, OnValidate } from '@monaco-editor/react'
import type { editor } from 'monaco-editor'
import { skillsApi } from '@/services/api'

interface Skill {
  id: number
  skill_id: string
  skill_name: string
  domain: string
  dsl_content: Record<string, unknown>
  dsl_version: string
  status: string
}

interface ValidationError {
  line: number
  column: number
  message: string
}

export default function SkillEditor() {
  const { skillId } = useParams<{ skillId: string }>()
  const navigate = useNavigate()
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)
  
  const [data, setData] = useState<Skill | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dslText, setDslText] = useState('')
  const [originalDslText, setOriginalDslText] = useState('')
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([])
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [hasChanges, setHasChanges] = useState(false)
  const [theme, setTheme] = useState<'vs' | 'vs-dark'>('vs')

  useEffect(() => {
    loadData()
  }, [skillId])

  useEffect(() => {
    setHasChanges(dslText !== originalDslText)
  }, [dslText, originalDslText])

  const loadData = async () => {
    try {
      const res = await skillsApi.detail(skillId!)
      setData(res as Skill)
      const formattedJson = JSON.stringify((res as Skill).dsl_content, null, 2)
      setDslText(formattedJson)
      setOriginalDslText(formattedJson)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 编辑器挂载回调
  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor
    
    // 添加快捷键
    editor.addCommand(
      // Ctrl/Cmd + S 保存
      editor.getModel()?.getLanguageId() === 'json' ? 2097 : 2097,
      () => {
        handleSave()
      }
    )
  }

  // 验证回调
  const handleValidate: OnValidate = (markers) => {
    const errors = markers.map(marker => ({
      line: marker.startLineNumber,
      column: marker.startColumn,
      message: marker.message
    }))
    setValidationErrors(errors)
  }

  // 格式化JSON
  const handleFormat = () => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument')?.run()
    }
  }

  // 撤销
  const handleUndo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'undo', null)
    }
  }

  // 重做
  const handleRedo = () => {
    if (editorRef.current) {
      editorRef.current.trigger('keyboard', 'redo', null)
    }
  }

  // 复制全部
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(dslText)
      message.success('已复制到剪贴板')
    } catch (e) {
      message.error('复制失败')
    }
  }

  // 保存
  const handleSave = async () => {
    // 检查是否有语法错误
    if (validationErrors.length > 0) {
      Modal.error({
        title: 'JSON格式错误',
        content: (
          <div className="max-h-60 overflow-auto">
            {validationErrors.map((err, idx) => (
              <div key={idx} className="text-red-500 mb-1">
                第 {err.line} 行: {err.message}
              </div>
            ))}
          </div>
        )
      })
      return
    }

    // 验证JSON格式
    let dslContent: Record<string, unknown>
    try {
      dslContent = JSON.parse(dslText)
    } catch (e) {
      message.error('JSON解析失败: ' + (e as Error).message)
      return
    }

    // DSL结构校验
    const schemaErrors = validateDslSchema(dslContent)
    if (schemaErrors.length > 0) {
      Modal.confirm({
        title: 'DSL结构警告',
        icon: <WarningOutlined style={{ color: '#faad14' }} />,
        content: (
          <div>
            <p className="mb-2">检测到以下结构问题，是否继续保存？</p>
            <div className="max-h-40 overflow-auto bg-yellow-50 p-2 rounded text-sm">
              {schemaErrors.map((err, idx) => (
                <div key={idx} className="text-yellow-700 mb-1">- {err}</div>
              ))}
            </div>
          </div>
        ),
        onOk: () => doSave(dslContent),
        okText: '继续保存',
        cancelText: '取消'
      })
      return
    }

    await doSave(dslContent)
  }

  const doSave = async (dslContent: Record<string, unknown>) => {
    setSaving(true)
    try {
      await skillsApi.update(skillId!, { dsl_content: dslContent })
      message.success('保存成功，已创建新版本')
      setOriginalDslText(dslText)
      navigate(`/skills/${skillId}`)
    } catch (error) {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  // DSL结构校验
  const validateDslSchema = (dsl: Record<string, unknown>): string[] => {
    const errors: string[] = []
    
    // 必需字段检查
    const requiredFields = ['skillId', 'skillName', 'domain']
    requiredFields.forEach(field => {
      if (!dsl[field]) {
        errors.push(`缺少必需字段: ${field}`)
      }
    })

    // 建议字段检查
    const suggestedFields = ['intentRecognition', 'attributeExtraction', 'categoryMapping']
    suggestedFields.forEach(field => {
      if (!dsl[field]) {
        errors.push(`建议添加字段: ${field}`)
      }
    })

    // intentRecognition结构检查
    if (dsl.intentRecognition) {
      const ir = dsl.intentRecognition as Record<string, unknown>
      if (!ir.keywords && !ir.patterns) {
        errors.push('intentRecognition 应包含 keywords 或 patterns')
      }
    }

    // attributeExtraction结构检查
    if (dsl.attributeExtraction) {
      const ae = dsl.attributeExtraction as Record<string, Record<string, unknown>>
      Object.entries(ae).forEach(([attrName, config]) => {
        if (!config.type) {
          errors.push(`属性 "${attrName}" 缺少 type 字段`)
        }
        if (!config.patterns || !(config.patterns as unknown[]).length) {
          errors.push(`属性 "${attrName}" 缺少有效的 patterns`)
        }
      })
    }

    return errors
  }

  // 全屏切换
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen)
  }

  // 返回确认
  const handleBack = () => {
    if (hasChanges) {
      Modal.confirm({
        title: '确认离开',
        content: '您有未保存的修改，确定要离开吗？',
        onOk: () => navigate(`/skills/${skillId}`),
        okText: '确定离开',
        cancelText: '继续编辑'
      })
    } else {
      navigate(`/skills/${skillId}`)
    }
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

  const editorContent = (
    <div className={isFullscreen ? 'fixed inset-0 z-50 bg-white p-4' : ''}>
      <Card 
        title={
          <div className="flex items-center justify-between">
            <span>编辑 Skill DSL - {data.skill_name}</span>
            {hasChanges && (
              <span className="text-orange-500 text-sm ml-4">
                <WarningOutlined /> 有未保存的修改
              </span>
            )}
          </div>
        }
        extra={
          <Space>
            <Select
              value={theme}
              onChange={setTheme}
              size="small"
              options={[
                { value: 'vs', label: '浅色主题' },
                { value: 'vs-dark', label: '深色主题' }
              ]}
              style={{ width: 100 }}
            />
            <Tooltip title="全屏">
              <Button 
                icon={isFullscreen ? <CompressOutlined /> : <ExpandOutlined />} 
                onClick={toggleFullscreen}
                size="small"
              />
            </Tooltip>
          </Space>
        }
        className="h-full"
        styles={{ body: { padding: isFullscreen ? '12px' : undefined, height: isFullscreen ? 'calc(100vh - 140px)' : undefined } }}
      >
        {/* 工具栏 */}
        <div className="flex justify-between items-center mb-3 pb-3 border-b">
          <Space>
            <Tooltip title="撤销 (Ctrl+Z)">
              <Button icon={<UndoOutlined />} onClick={handleUndo} size="small" />
            </Tooltip>
            <Tooltip title="重做 (Ctrl+Y)">
              <Button icon={<RedoOutlined />} onClick={handleRedo} size="small" />
            </Tooltip>
            <Tooltip title="格式化 (Shift+Alt+F)">
              <Button icon={<FormatPainterOutlined />} onClick={handleFormat} size="small">
                格式化
              </Button>
            </Tooltip>
            <Tooltip title="复制全部">
              <Button icon={<CopyOutlined />} onClick={handleCopy} size="small" />
            </Tooltip>
          </Space>
          
          <Space>
            {/* 校验状态 */}
            {validationErrors.length === 0 ? (
              <span className="text-green-500 text-sm">
                <CheckCircleOutlined /> JSON格式正确
              </span>
            ) : (
              <span className="text-red-500 text-sm">
                <WarningOutlined /> 发现 {validationErrors.length} 个错误
              </span>
            )}
          </Space>
        </div>

        {/* 错误提示 */}
        {validationErrors.length > 0 && (
          <Alert
            type="error"
            className="mb-3"
            message="JSON语法错误"
            description={
              <div className="max-h-20 overflow-auto text-sm">
                {validationErrors.slice(0, 3).map((err, idx) => (
                  <div key={idx}>
                    第 {err.line} 行，第 {err.column} 列: {err.message}
                  </div>
                ))}
                {validationErrors.length > 3 && (
                  <div>...还有 {validationErrors.length - 3} 个错误</div>
                )}
              </div>
            }
            showIcon
          />
        )}

        {/* Monaco编辑器 */}
        <Editor
          height={isFullscreen ? 'calc(100vh - 280px)' : '550px'}
          language="json"
          theme={theme}
          value={dslText}
          onChange={(value) => setDslText(value || '')}
          onMount={handleEditorMount}
          onValidate={handleValidate}
          options={{
            minimap: { enabled: true },
            fontSize: 14,
            fontFamily: 'JetBrains Mono, Fira Code, Monaco, Consolas, monospace',
            lineNumbers: 'on',
            wordWrap: 'on',
            automaticLayout: true,
            formatOnPaste: true,
            formatOnType: false,
            scrollBeyondLastLine: false,
            folding: true,
            foldingStrategy: 'indentation',
            bracketPairColorization: { enabled: true },
            renderLineHighlight: 'all',
            tabSize: 2,
            insertSpaces: true,
            suggest: {
              showKeywords: true,
            }
          }}
        />

        <div className="mt-3 text-gray-400 text-sm flex justify-between">
          <span>提示: 修改DSL内容后点击保存，系统会自动创建新版本</span>
          <span>快捷键: Ctrl+S 保存 | Shift+Alt+F 格式化 | Ctrl+Z 撤销</span>
        </div>
      </Card>
    </div>
  )

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={handleBack}
        >
          返回详情
        </Button>
        <Space>
          <Button onClick={() => {
            setDslText(originalDslText)
            message.info('已重置为原始内容')
          }} disabled={!hasChanges}>
            重置
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={handleSave}
            disabled={validationErrors.length > 0}
          >
            保存
          </Button>
        </Space>
      </div>

      {editorContent}
    </div>
  )
}
