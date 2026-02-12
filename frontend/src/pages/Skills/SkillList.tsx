import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, Tag, Space, Input, Select, message, Popconfirm } from 'antd'
import { SearchOutlined, DeleteOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons'
import BaseTable from '@/components/BaseTable'
import { skillsApi } from '@/services/api'

interface Skill {
  id: number
  skill_id: string
  skill_name: string
  domain: string
  priority: number
  dsl_version: string
  status: string
  created_at: string
}

export default function SkillList() {
  const [data, setData] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [domain, setDomain] = useState<string | undefined>()

  useEffect(() => {
    loadData()
  }, [page, pageSize, keyword, domain])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await skillsApi.list({ page, page_size: pageSize, keyword, domain }) as {
        items: Skill[]
        total: number
      }
      setData(res.items || [])
      setTotal(res.total || 0)
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (skillId: string) => {
    try {
      await skillsApi.delete(skillId)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleActivate = async (skillId: string) => {
    try {
      await skillsApi.activate(skillId)
      message.success('激活成功')
      loadData()
    } catch (error) {
      message.error('激活失败')
    }
  }

  const handleDeactivate = async (skillId: string) => {
    try {
      await skillsApi.deactivate(skillId)
      message.success('停用成功')
      loadData()
    } catch (error) {
      message.error('停用失败')
    }
  }

  const columns = [
    {
      title: 'Skill ID',
      dataIndex: 'skill_id',
      key: 'skill_id',
      width: 200,
    },
    {
      title: '名称',
      dataIndex: 'skill_name',
      key: 'skill_name',
      width: 250,
    },
    {
      title: '领域',
      dataIndex: 'domain',
      key: 'domain',
      width: 100,
      render: (domain: string) => (
        <Tag>{domain === 'pipe' ? '管材' : domain === 'fastener' ? '紧固件' : domain || '未分类'}</Tag>
      ),
    },
    {
      title: '版本',
      dataIndex: 'dsl_version',
      key: 'dsl_version',
      width: 80,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          testing: { color: 'blue', text: '测试中' },
          active: { color: 'green', text: '已激活' },
          deprecated: { color: 'red', text: '已停用' },
        }
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 250,
      render: (_: unknown, record: Skill) => (
        <Space>
          <Link to={`/skills/${record.skill_id}`}>
            <Button type="link" size="small" icon={<EyeOutlined />}>
              查看
            </Button>
          </Link>
          <Link to={`/skills/${record.skill_id}/edit`}>
            <Button type="link" size="small" icon={<EditOutlined />}>
              编辑
            </Button>
          </Link>
          {record.status !== 'active' ? (
            <Button type="link" size="small" onClick={() => handleActivate(record.skill_id)}>
              激活
            </Button>
          ) : (
            <Button type="link" size="small" onClick={() => handleDeactivate(record.skill_id)}>
              停用
            </Button>
          )}
          <Popconfirm
            title="确定删除吗?"
            onConfirm={() => handleDelete(record.skill_id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex justify-between items-center mb-4">
          <div className="flex gap-4">
            <Input
              placeholder="搜索Skill ID或名称"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 250 }}
              allowClear
            />
            <Select
              placeholder="选择领域"
              style={{ width: 150 }}
              value={domain}
              onChange={setDomain}
              allowClear
              options={[
                { value: 'pipe', label: '管材' },
                { value: 'fastener', label: '紧固件' },
              ]}
            />
          </div>
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
    </div>
  )
}
