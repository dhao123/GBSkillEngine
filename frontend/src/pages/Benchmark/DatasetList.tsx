import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Card, Tag, Space, Input, Select, message, Popconfirm, Modal, Form, Progress } from 'antd'
import { SearchOutlined, DeleteOutlined, EyeOutlined, PlusOutlined, ThunderboltOutlined } from '@ant-design/icons'
import BaseTable from '@/components/BaseTable'
import { benchmarkApi, skillsApi } from '@/services/api'

interface Dataset {
  id: number
  dataset_code: string
  dataset_name: string
  description?: string
  skill_id?: number
  source_type: string
  status: string
  total_cases: number
  difficulty_distribution?: Record<string, number>
  created_at: string
}

interface Skill {
  id: number
  skill_id: string
  skill_name: string
}

export default function DatasetList() {
  const navigate = useNavigate()
  const [data, setData] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [status, setStatus] = useState<string | undefined>()
  
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [createForm] = Form.useForm()
  const [skills, setSkills] = useState<Skill[]>([])
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadData()
    loadSkills()
  }, [page, pageSize, keyword, status])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await benchmarkApi.listDatasets({ page, page_size: pageSize, keyword, status }) as {
        items: Dataset[]
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

  const loadSkills = async () => {
    try {
      const res = await skillsApi.list({ page: 1, page_size: 100, status: 'active' }) as {
        items: Skill[]
      }
      setSkills(res.items || [])
    } catch {
      // ignore
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await benchmarkApi.deleteDataset(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleCreate = async (values: Record<string, unknown>) => {
    setCreating(true)
    try {
      const res = await benchmarkApi.createDataset(values) as Dataset
      message.success('创建成功')
      setCreateModalOpen(false)
      createForm.resetFields()
      navigate(`/benchmark/datasets/${res.id}`)
    } catch (error) {
      message.error('创建失败')
    } finally {
      setCreating(false)
    }
  }

  const columns = [
    {
      title: '数据集编码',
      dataIndex: 'dataset_code',
      key: 'dataset_code',
      width: 180,
    },
    {
      title: '名称',
      dataIndex: 'dataset_name',
      key: 'dataset_name',
      width: 250,
    },
    {
      title: '来源类型',
      dataIndex: 'source_type',
      key: 'source_type',
      width: 100,
      render: (type: string) => {
        const typeMap: Record<string, { color: string; text: string }> = {
          seed: { color: 'blue', text: '种子数据' },
          generated: { color: 'purple', text: '自动生成' },
          mixed: { color: 'orange', text: '混合' },
        }
        const { color, text } = typeMap[type] || { color: 'default', text: type }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '用例数',
      dataIndex: 'total_cases',
      key: 'total_cases',
      width: 100,
      render: (count: number, record: Dataset) => {
        if (!record.difficulty_distribution) {
          return count
        }
        const dist = record.difficulty_distribution
        return (
          <div className="text-sm">
            <div className="font-medium">{count}</div>
            <div className="text-gray-400 text-xs">
              E:{dist.easy || 0} M:{dist.medium || 0} H:{dist.hard || 0}
            </div>
          </div>
        )
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          ready: { color: 'green', text: '就绪' },
          archived: { color: 'red', text: '已归档' },
        }
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: Dataset) => (
        <Space>
          <Link to={`/benchmark/datasets/${record.id}`}>
            <Button type="link" size="small" icon={<EyeOutlined />}>
              查看
            </Button>
          </Link>
          <Link to={`/benchmark/datasets/${record.id}?tab=run`}>
            <Button type="link" size="small" icon={<ThunderboltOutlined />}>
              评测
            </Button>
          </Link>
          <Popconfirm
            title="确定删除吗?"
            onConfirm={() => handleDelete(record.id)}
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
              placeholder="搜索数据集"
              prefix={<SearchOutlined />}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ width: 250 }}
              allowClear
            />
            <Select
              placeholder="状态筛选"
              style={{ width: 120 }}
              value={status}
              onChange={setStatus}
              allowClear
              options={[
                { value: 'draft', label: '草稿' },
                { value: 'ready', label: '就绪' },
                { value: 'archived', label: '已归档' },
              ]}
            />
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalOpen(true)}>
            新建数据集
          </Button>
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
        title="新建评测数据集"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        footer={null}
        width={500}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreate}
        >
          <Form.Item
            name="dataset_code"
            label="数据集编码"
            rules={[{ required: true, message: '请输入数据集编码' }]}
          >
            <Input placeholder="如: DS_PIPE_001" />
          </Form.Item>
          <Form.Item
            name="dataset_name"
            label="数据集名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="如: PVC管材物料解析测试集" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="数据集说明..." />
          </Form.Item>
          <Form.Item
            name="skill_id"
            label="关联Skill"
          >
            <Select
              placeholder="选择关联的Skill"
              allowClear
              options={skills.map(s => ({ value: s.id, label: `${s.skill_id} - ${s.skill_name}` }))}
            />
          </Form.Item>
          <Form.Item
            name="source_type"
            label="来源类型"
            initialValue="mixed"
          >
            <Select
              options={[
                { value: 'seed', label: '种子数据' },
                { value: 'generated', label: '自动生成' },
                { value: 'mixed', label: '混合' },
              ]}
            />
          </Form.Item>
          <Form.Item className="mb-0 text-right">
            <Space>
              <Button onClick={() => setCreateModalOpen(false)}>取消</Button>
              <Button type="primary" htmlType="submit" loading={creating}>
                创建
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
