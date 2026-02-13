/**
 * 节点详情面板组件
 */
import { Drawer, Descriptions, Tag, Empty } from 'antd'
import { CloseOutlined } from '@ant-design/icons'
import type { Graph3DNode } from './types'

// 节点类型颜色
const NODE_COLORS: Record<string, string> = {
  Standard: '#00d4ff',
  Skill: '#ff6b6b',
  Category: '#7c3aed',
  Domain: '#f59e0b',
  TimeSlice: '#6366f1'
}

// 节点类型中文名
const NODE_TYPE_NAMES: Record<string, string> = {
  Standard: '国标',
  Skill: '技能',
  Category: '类目',
  Domain: '领域',
  TimeSlice: '时间'
}

interface NodeDetailPanelProps {
  visible: boolean
  node: Graph3DNode | null
  onClose: () => void
}

export default function NodeDetailPanel({
  visible,
  node,
  onClose
}: NodeDetailPanelProps) {
  // 渲染属性值
  const renderPropertyValue = (value: unknown) => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'boolean') return value ? '是' : '否'
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  // 过滤内部属性
  const filterProperties = (props: Record<string, unknown>) => {
    const internalKeys = ['x', 'y', 'z', 'fx', 'fy', 'fz', 'vx', 'vy', 'vz', 'index', 'color']
    return Object.entries(props).filter(([key]) => !internalKeys.includes(key))
  }

  return (
    <Drawer
      title={
        <div className="flex items-center gap-2">
          <span 
            className="inline-block w-4 h-4 rounded" 
            style={{ backgroundColor: node ? NODE_COLORS[node.nodeType] : '#666' }} 
          />
          <span>节点详情</span>
        </div>
      }
      placement="right"
      width={400}
      open={visible}
      onClose={onClose}
      closeIcon={<CloseOutlined />}
    >
      {node ? (
        <div className="space-y-4">
          {/* 基本信息 */}
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="节点ID">{node.id}</Descriptions.Item>
            <Descriptions.Item label="节点名称">{node.label}</Descriptions.Item>
            <Descriptions.Item label="节点类型">
              <Tag color={NODE_COLORS[node.nodeType]}>
                {NODE_TYPE_NAMES[node.nodeType] || node.nodeType}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          {/* 3D位置 */}
          <div>
            <div className="font-medium mb-2 text-gray-600">3D坐标</div>
            <Descriptions column={3} bordered size="small">
              <Descriptions.Item label="X">{node.position.x.toFixed(1)}</Descriptions.Item>
              <Descriptions.Item label="Y">{node.position.y.toFixed(1)}</Descriptions.Item>
              <Descriptions.Item label="Z">{node.position.z.toFixed(1)}</Descriptions.Item>
            </Descriptions>
          </div>

          {/* 属性详情 */}
          <div>
            <div className="font-medium mb-2 text-gray-600">属性详情</div>
            {filterProperties(node.properties).length > 0 ? (
              <Descriptions column={1} bordered size="small">
                {filterProperties(node.properties).map(([key, value]) => (
                  <Descriptions.Item key={key} label={key}>
                    {renderPropertyValue(value)}
                  </Descriptions.Item>
                ))}
              </Descriptions>
            ) : (
              <Empty description="暂无属性" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </div>
        </div>
      ) : (
        <Empty description="请选择一个节点" />
      )}
    </Drawer>
  )
}
