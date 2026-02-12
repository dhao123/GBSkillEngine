import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Button, Spin, message, Input } from 'antd'
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons'
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

export default function SkillEditor() {
  const { skillId } = useParams<{ skillId: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<Skill | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dslText, setDslText] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [skillId])

  const loadData = async () => {
    try {
      const res = await skillsApi.detail(skillId!)
      setData(res as Skill)
      setDslText(JSON.stringify((res as Skill).dsl_content, null, 2))
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    // 验证JSON格式
    try {
      const dslContent = JSON.parse(dslText)
      setError(null)

      setSaving(true)
      await skillsApi.update(skillId!, { dsl_content: dslContent })
      message.success('保存成功')
      navigate(`/skills/${skillId}`)
    } catch (e) {
      if (e instanceof SyntaxError) {
        setError('JSON格式错误: ' + e.message)
      } else {
        message.error('保存失败')
      }
    } finally {
      setSaving(false)
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

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate(`/skills/${skillId}`)}
        >
          返回详情
        </Button>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          loading={saving}
          onClick={handleSave}
        >
          保存
        </Button>
      </div>

      <Card title={`编辑 Skill DSL - ${data.skill_name}`}>
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-600 rounded">
            {error}
          </div>
        )}
        <Input.TextArea
          value={dslText}
          onChange={(e) => setDslText(e.target.value)}
          rows={30}
          style={{ fontFamily: 'monospace', fontSize: 13 }}
        />
        <div className="mt-2 text-gray-400 text-sm">
          提示: 修改DSL内容后点击保存，系统会自动创建新版本
        </div>
      </Card>
    </div>
  )
}
