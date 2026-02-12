import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Select, Upload, Button, message } from 'antd'
import { UploadOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd/es/upload/interface'
import { standardsApi } from '@/services/api'

export default function StandardUpload() {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: Record<string, unknown>) => {
    if (fileList.length === 0) {
      message.error('请上传国标文档')
      return
    }

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', fileList[0].originFileObj as File)
      formData.append('standard_code', values.standard_code as string)
      formData.append('standard_name', values.standard_name as string)
      if (values.version_year) formData.append('version_year', values.version_year as string)
      if (values.domain) formData.append('domain', values.domain as string)
      if (values.product_scope) formData.append('product_scope', values.product_scope as string)

      await standardsApi.upload(formData)
      message.success('上传成功')
      navigate('/standards')
    } catch (error) {
      message.error('上传失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/standards')}
      >
        返回列表
      </Button>

      <Card title="上传国标文档">
        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          style={{ maxWidth: 600 }}
        >
          <Form.Item
            label="国标编号"
            name="standard_code"
            rules={[{ required: true, message: '请输入国标编号' }]}
          >
            <Input placeholder="例如: GB/T 4219.1-2021" />
          </Form.Item>

          <Form.Item
            label="标准名称"
            name="standard_name"
            rules={[{ required: true, message: '请输入标准名称' }]}
          >
            <Input placeholder="例如: 工业用聚氯乙烯管道系统" />
          </Form.Item>

          <Form.Item label="版本年份" name="version_year">
            <Input placeholder="例如: 2021" />
          </Form.Item>

          <Form.Item label="适用领域" name="domain">
            <Select
              placeholder="选择领域"
              options={[
                { value: 'pipe', label: '管材' },
                { value: 'fastener', label: '紧固件' },
                { value: 'valve', label: '阀门' },
                { value: 'general', label: '通用' },
              ]}
            />
          </Form.Item>

          <Form.Item label="产品范围" name="product_scope">
            <Input.TextArea rows={3} placeholder="描述该标准适用的产品范围" />
          </Form.Item>

          <Form.Item
            label="国标文档"
            required
          >
            <Upload
              fileList={fileList}
              onChange={({ fileList }) => setFileList(fileList)}
              beforeUpload={() => false}
              accept=".pdf,.doc,.docx"
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
            <div className="text-gray-400 text-sm mt-1">
              支持 PDF、Word 格式，最大 50MB
            </div>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading}>
              上传
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
