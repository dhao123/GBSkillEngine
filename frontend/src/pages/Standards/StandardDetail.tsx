import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Card, Descriptions, Tag, Button, Spin, message, Space, Modal, Progress, Steps } from 'antd'
import { 
  ArrowLeftOutlined, 
  ThunderboltOutlined, 
  FileTextOutlined, 
  DownloadOutlined,
  EyeOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'
import { standardsApi } from '@/services/api'

interface Standard {
  id: number
  standard_code: string
  standard_name: string
  version_year: string
  domain: string
  product_scope: string
  file_path: string
  file_type: string
  status: string
  created_at: string
  updated_at: string
}

export default function StandardDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [data, setData] = useState<Standard | null>(null)
  const [loading, setLoading] = useState(true)
  const [compiling, setCompiling] = useState(false)
  const [compileProgress, setCompileProgress] = useState(0)
  const [compileStep, setCompileStep] = useState(0)
  const [previewVisible, setPreviewVisible] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const res = await standardsApi.detail(Number(id))
      setData(res as Standard)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 编译进度模拟
  const simulateCompileProgress = () => {
    const steps = [
      { step: 0, progress: 10, delay: 200 },
      { step: 0, progress: 30, delay: 500 },
      { step: 1, progress: 50, delay: 800 },
      { step: 1, progress: 70, delay: 300 },
      { step: 2, progress: 85, delay: 500 },
      { step: 2, progress: 95, delay: 300 },
    ]
    
    let index = 0
    const timer = setInterval(() => {
      if (index < steps.length) {
        setCompileStep(steps[index].step)
        setCompileProgress(steps[index].progress)
        index++
      } else {
        clearInterval(timer)
      }
    }, steps[index]?.delay || 300)
    
    return timer
  }

  const handleCompile = async () => {
    setCompiling(true)
    setCompileProgress(0)
    setCompileStep(0)
    
    const timer = simulateCompileProgress()
    
    try {
      const res = await standardsApi.compile(Number(id)) as { skill_id: string }
      clearInterval(timer)
      setCompileStep(3)
      setCompileProgress(100)
      
      setTimeout(() => {
        message.success('编译成功')
        setCompiling(false)
        navigate(`/skills/${res.skill_id}`)
      }, 500)
    } catch (error) {
      clearInterval(timer)
      message.error('编译失败')
      setCompiling(false)
    }
  }

  // 打开文档预览
  const handlePreview = () => {
    if (data?.file_type === 'pdf') {
      setPreviewVisible(true)
    } else {
      // Word文档无法直接预览，提示下载
      message.info('Word文档暂不支持在线预览，请下载后查看')
      handleDownload()
    }
  }

  // 下载文档
  const handleDownload = () => {
    window.open(`/api/v1/standards/${id}/download`, '_blank')
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    )
  }

  if (!data) {
    return <div>国标不存在</div>
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    uploaded: { color: 'blue', text: '已上传' },
    compiled: { color: 'green', text: '已编译' },
    published: { color: 'purple', text: '已发布' },
  }

  const compileSteps = [
    { title: '文档解析', description: '解析PDF/Word文档' },
    { title: '结构分析', description: '识别标准规格结构' },
    { title: 'DSL生成', description: '生成Skill DSL配置' },
    { title: '完成', description: '编译完成' },
  ]

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/standards')}
        >
          返回列表
        </Button>
        <Space>
          {data.file_path && (
            <>
              <Button
                icon={<EyeOutlined />}
                onClick={handlePreview}
              >
                预览文档
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleDownload}
              >
                下载
              </Button>
            </>
          )}
          {data.status === 'uploaded' && (
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              loading={compiling}
              onClick={handleCompile}
            >
              编译为Skill
            </Button>
          )}
          {data.status === 'compiled' && (
            <Link to={`/skills/skill_${data.standard_code.replace(/[\/\.\-]/g, '_').toLowerCase()}`}>
              <Button type="primary" icon={<ThunderboltOutlined />}>
                查看Skill
              </Button>
            </Link>
          )}
        </Space>
      </div>

      <Card title="国标详情">
        <Descriptions column={2}>
          <Descriptions.Item label="国标编号">{data.standard_code}</Descriptions.Item>
          <Descriptions.Item label="标准名称">{data.standard_name}</Descriptions.Item>
          <Descriptions.Item label="版本年份">{data.version_year || '-'}</Descriptions.Item>
          <Descriptions.Item label="适用领域">
            <Tag>
              {data.domain === 'pipe' ? '管材' : data.domain === 'fastener' ? '紧固件' : data.domain || '未分类'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={statusMap[data.status]?.color || 'default'}>
              {statusMap[data.status]?.text || data.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="文件类型">
            {data.file_type ? (
              <Tag icon={<FileTextOutlined />}>{data.file_type.toUpperCase()}</Tag>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {new Date(data.created_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {new Date(data.updated_at).toLocaleString()}
          </Descriptions.Item>
          <Descriptions.Item label="产品范围" span={2}>
            {data.product_scope || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 编译进度弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <SyncOutlined spin={compileProgress < 100} />
            <span>编译国标为 Skill</span>
          </div>
        }
        open={compiling}
        closable={false}
        footer={null}
        width={600}
      >
        <div className="py-6">
          <div className="mb-6">
            <Progress 
              percent={compileProgress} 
              status={compileProgress === 100 ? 'success' : 'active'}
              strokeColor={{
                '0%': '#3462FE',
                '100%': '#52c41a',
              }}
            />
          </div>
          
          <Steps
            current={compileStep}
            items={compileSteps.map((step, index) => ({
              title: step.title,
              description: step.description,
              icon: index < compileStep ? (
                <CheckCircleOutlined style={{ color: '#52c41a' }} />
              ) : index === compileStep && compileProgress < 100 ? (
                <LoadingOutlined style={{ color: '#3462FE' }} />
              ) : undefined
            }))}
          />
          
          <div className="mt-6 text-center text-gray-500">
            {compileProgress < 100 ? (
              <span>正在处理 {data.standard_code}...</span>
            ) : (
              <span className="text-green-500">编译完成！即将跳转到Skill详情页...</span>
            )}
          </div>
        </div>
      </Modal>

      {/* PDF预览弹窗 */}
      <Modal
        title={
          <div className="flex items-center gap-2">
            <FileTextOutlined />
            <span>文档预览 - {data.standard_code}</span>
          </div>
        }
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width="90%"
        style={{ top: 20 }}
        footer={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleDownload}>
              下载文档
            </Button>
            <Button onClick={() => setPreviewVisible(false)}>
              关闭
            </Button>
          </Space>
        }
        styles={{ body: { padding: 0, height: 'calc(100vh - 200px)' } }}
      >
        <iframe
          src={`/api/v1/standards/${id}/preview`}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
          }}
          title="PDF预览"
        />
      </Modal>
    </div>
  )
}
