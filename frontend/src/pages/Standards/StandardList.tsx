import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, Tag, Space, Input, Select, message, Popconfirm } from 'antd'
import { PlusOutlined, SearchOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import BaseTable from '@/components/BaseTable'
import { standardsApi } from '@/services/api'

interface Standard {
  id: number
  standard_code: string
  standard_name: string
  version_year: string
  domain: string
  status: string
  created_at: string
}

export default function StandardList() {
  const [data, setData] = useState<Standard[]>([])
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
      const res = await standardsApi.list({ page, page_size: pageSize, keyword, domain }) as {
        items: Standard[]
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

  const handleDelete = async (id: number) => {
    try {
      await standardsApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleCompile = async (id: number) => {
    try {
      await standardsApi.compile(id)
      message.success('编译成功')
      loadData()
    } catch (error) {
      message.error('编译失败')
    }
  }

  const columns = [
    {
      title: '国标编号',
      dataIndex: 'standard_code',
      key: 'standard_code',
      width: 150,
    },
    {
      title: '标准名称',
      dataIndex: 'standard_name',
      key: 'standard_name',
      width: 300,
    },
    {
      title: '版本年份',
      dataIndex: 'version_year',
      key: 'version_year',
      width: 100,
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
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          uploaded: { color: 'blue', text: '已上传' },
          compiled: { color: 'green', text: '已编译' },
          published: { color: 'purple', text: '已发布' },
        }
        const { color, text } = statusMap[status] || { color: 'default', text: status }
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: unknown, record: Standard) => (
        <Space>
          <Link to={`/standards/${record.id}`}>
            <Button type="link" size="small" icon={<EyeOutlined />}>
              查看
            </Button>
          </Link>
          {record.status === 'uploaded' && (
            <Button type="link" size="small" onClick={() => handleCompile(record.id)}>
              编译
            </Button>
          )}
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
              placeholder="搜索国标编号或名称"
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
          <Link to="/standards/upload">
            <Button type="primary" icon={<PlusOutlined />}>
              上传国标
            </Button>
          </Link>
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
