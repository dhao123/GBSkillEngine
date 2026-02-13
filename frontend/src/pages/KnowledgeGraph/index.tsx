import { useEffect, useState, useRef, useCallback } from 'react'
import { Card, Spin, message, Drawer, Descriptions, Tag, Input, Select, Radio, Empty } from 'antd'
import { SearchOutlined, CloseOutlined } from '@ant-design/icons'
import G6 from '@antv/g6'
import { knowledgeGraphApi } from '@/services/api'

interface Node {
  id: string
  label: string
  properties: Record<string, unknown>
}

interface Edge {
  source: string
  target: string
  type: string
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
}

interface GraphNode {
  id: string
  label: string
  nodeType: string
  properties: Record<string, unknown>
  style: { fill: string }
}

// 节点颜色映射
const COLOR_MAP: Record<string, string> = {
  Standard: '#3462FE',
  Category: '#9D34FE',
  Attribute: '#52c41a',
  DimensionTable: '#faad14',
  Material: '#1890ff',
  MaterialInstance: '#13c2c2',
}

// 节点类型中文名映射
const NODE_TYPE_NAMES: Record<string, string> = {
  Standard: '国标',
  Category: '类目',
  Attribute: '属性',
  DimensionTable: '尺寸表',
  Material: '物料',
  MaterialInstance: '物料实例',
}

// 布局配置
const LAYOUT_OPTIONS = [
  { value: 'force', label: '力导向' },
  { value: 'dagre', label: '层级' },
  { value: 'circular', label: '圆形' },
  { value: 'radial', label: '辐射' },
]

export default function KnowledgeGraph() {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<InstanceType<typeof G6.Graph> | null>(null)
  const [loading, setLoading] = useState(true)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  
  // 节点详情面板状态
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  
  // 搜索状态
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchResults, setSearchResults] = useState<GraphNode[]>([])
  
  // 过滤状态
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>(Object.keys(COLOR_MAP))
  const [selectedRelTypes, setSelectedRelTypes] = useState<string[]>([])
  const [availableRelTypes, setAvailableRelTypes] = useState<string[]>([])
  
  // 布局状态
  const [layoutType, setLayoutType] = useState('force')

  useEffect(() => {
    loadData()
    return () => {
      if (graphRef.current) {
        graphRef.current.destroy()
      }
    }
  }, [])

  const loadData = async () => {
    try {
      const res = await knowledgeGraphApi.visualize() as GraphData
      setGraphData(res)
      // 提取所有关系类型
      const relTypes = [...new Set(res.edges.map(e => e.type))]
      setAvailableRelTypes(relTypes)
      setSelectedRelTypes(relTypes)
      renderGraph(res)
    } catch (error) {
      message.error('加载知识图谱失败')
    } finally {
      setLoading(false)
    }
  }

  // 获取布局配置
  const getLayoutConfig = useCallback((type: string) => {
    switch (type) {
      case 'dagre':
        return { type: 'dagre', rankdir: 'TB', nodesep: 50, ranksep: 80 }
      case 'circular':
        return { type: 'circular', radius: 200 }
      case 'radial':
        return { type: 'radial', unitRadius: 100, linkDistance: 200 }
      case 'force':
      default:
        return { type: 'force', preventOverlap: true, nodeSpacing: 80, linkDistance: 150 }
    }
  }, [])

  // 转换节点数据
  const transformNodes = useCallback((nodes: Node[]): GraphNode[] => {
    return nodes.map((node) => ({
      id: node.id,
      label: String(node.properties.standardCode || node.properties.categoryName || 
             node.properties.attributeName || node.label),
      nodeType: node.label,
      properties: node.properties,
      style: {
        fill: COLOR_MAP[node.label] || '#666',
      },
    }))
  }, [])

  const renderGraph = useCallback((data: GraphData, layout?: string) => {
    if (!containerRef.current) return

    // 销毁旧图实例
    if (graphRef.current) {
      graphRef.current.destroy()
      graphRef.current = null
    }

    const container = containerRef.current
    const width = container.scrollWidth
    const height = container.scrollHeight || 600

    // 转换数据格式
    const nodes = transformNodes(data.nodes)
    const edges = data.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.type,
      relType: edge.type,
    }))

    graphRef.current = new G6.Graph({
      container,
      width,
      height,
      fitView: true,
      fitViewPadding: 50,
      layout: getLayoutConfig(layout || layoutType),
      defaultNode: {
        size: 50,
        style: {
          lineWidth: 2,
          stroke: '#fff',
        },
        labelCfg: {
          position: 'bottom',
          offset: 5,
          style: {
            fill: '#333',
            fontSize: 12,
          },
        },
      },
      defaultEdge: {
        style: {
          stroke: '#e2e2e2',
          lineWidth: 1,
          endArrow: true,
        },
        labelCfg: {
          autoRotate: true,
          style: {
            fill: '#999',
            fontSize: 10,
          },
        },
      },
      modes: {
        default: ['drag-canvas', 'zoom-canvas', 'drag-node'],
      },
      nodeStateStyles: {
        selected: {
          stroke: '#ff4d4f',
          lineWidth: 3,
        },
        highlight: {
          stroke: '#1890ff',
          lineWidth: 3,
        },
      },
    })

    graphRef.current.data({ nodes, edges })
    graphRef.current.render()

    // 节点点击事件 - 显示详情面板
    graphRef.current.on('node:click', (evt) => {
      const nodeModel = evt.item?.getModel() as GraphNode | undefined
      if (nodeModel) {
        // 清除之前的选中状态
        graphRef.current?.getNodes().forEach(n => {
          graphRef.current?.clearItemStates(n, ['selected'])
        })
        // 设置当前节点选中状态
        graphRef.current?.setItemState(evt.item!, 'selected', true)
        
        setSelectedNode(nodeModel)
        setDetailVisible(true)
      }
    })

    // 画布点击 - 取消选中
    graphRef.current.on('canvas:click', () => {
      graphRef.current?.getNodes().forEach(n => {
        graphRef.current?.clearItemStates(n, ['selected'])
      })
    })
  }, [layoutType, getLayoutConfig, transformNodes])

  // 搜索节点
  const handleSearch = useCallback((keyword: string) => {
    setSearchKeyword(keyword)
    if (!graphData || !keyword.trim()) {
      setSearchResults([])
      // 清除高亮
      graphRef.current?.getNodes().forEach(n => {
        graphRef.current?.clearItemStates(n, ['highlight'])
      })
      return
    }

    const nodes = transformNodes(graphData.nodes)
    const results = nodes.filter(node => {
      const searchStr = keyword.toLowerCase()
      return (
        node.label.toLowerCase().includes(searchStr) ||
        node.nodeType.toLowerCase().includes(searchStr) ||
        Object.values(node.properties).some(v => 
          String(v).toLowerCase().includes(searchStr)
        )
      )
    })
    setSearchResults(results)

    // 高亮匹配的节点
    graphRef.current?.getNodes().forEach(n => {
      const model = n.getModel()
      const isMatch = results.some(r => r.id === model.id)
      graphRef.current?.setItemState(n, 'highlight', isMatch)
    })
  }, [graphData, transformNodes])

  // 定位到节点
  const focusNode = useCallback((nodeId: string) => {
    if (!graphRef.current) return
    const node = graphRef.current.findById(nodeId)
    if (node) {
      graphRef.current.focusItem(node, true, { duration: 300 })
      graphRef.current.getNodes().forEach(n => {
        graphRef.current?.clearItemStates(n, ['selected'])
      })
      graphRef.current.setItemState(node, 'selected', true)
      
      const model = node.getModel() as GraphNode
      setSelectedNode(model)
      setDetailVisible(true)
    }
  }, [])

  // 切换布局
  const handleLayoutChange = useCallback((type: string) => {
    setLayoutType(type)
    if (graphData) {
      renderGraph(graphData, type)
    }
  }, [graphData, renderGraph])

  // 节点类型过滤
  const handleNodeTypeFilter = useCallback((types: string[]) => {
    setSelectedNodeTypes(types)
    if (!graphData || !graphRef.current) return

    graphRef.current.getNodes().forEach(node => {
      const model = node.getModel() as GraphNode
      const visible = types.includes(model.nodeType)
      if (visible) {
        graphRef.current?.showItem(node)
      } else {
        graphRef.current?.hideItem(node)
      }
    })
  }, [graphData])

  // 关系类型过滤
  const handleRelTypeFilter = useCallback((types: string[]) => {
    setSelectedRelTypes(types)
    if (!graphRef.current) return

    graphRef.current.getEdges().forEach(edge => {
      const model = edge.getModel() as { relType: string }
      const visible = types.includes(model.relType)
      if (visible) {
        graphRef.current?.showItem(edge)
      } else {
        graphRef.current?.hideItem(edge)
      }
    })
  }, [])

  // 渲染属性值
  const renderPropertyValue = (value: unknown) => {
    if (value === null || value === undefined) return '-'
    if (typeof value === 'boolean') return value ? '是' : '否'
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  return (
    <div className="flex gap-4">
      {/* 主图谱区域 */}
      <div className="flex-1">
        <Card
          title="MRO国标知识图谱"
          extra={
            <div className="flex items-center gap-4">
              {/* 布局切换 */}
              <Radio.Group 
                value={layoutType} 
                onChange={e => handleLayoutChange(e.target.value)}
                size="small"
                optionType="button"
              >
                {LAYOUT_OPTIONS.map(opt => (
                  <Radio.Button key={opt.value} value={opt.value}>{opt.label}</Radio.Button>
                ))}
              </Radio.Group>
            </div>
          }
        >
          {/* 工具栏 */}
          <div className="flex gap-4 mb-4">
            {/* 搜索框 */}
            <Input
              placeholder="搜索节点..."
              prefix={<SearchOutlined />}
              value={searchKeyword}
              onChange={e => handleSearch(e.target.value)}
              style={{ width: 200 }}
              allowClear
            />
            
            {/* 节点类型过滤 */}
            <Select
              mode="multiple"
              placeholder="节点类型"
              value={selectedNodeTypes}
              onChange={handleNodeTypeFilter}
              style={{ minWidth: 200 }}
              maxTagCount={2}
              options={Object.entries(NODE_TYPE_NAMES).map(([value, label]) => ({
                value,
                label: (
                  <span className="flex items-center gap-2">
                    <span 
                      className="inline-block w-3 h-3 rounded" 
                      style={{ backgroundColor: COLOR_MAP[value] }} 
                    />
                    {label}
                  </span>
                ),
              }))}
            />
            
            {/* 关系类型过滤 */}
            <Select
              mode="multiple"
              placeholder="关系类型"
              value={selectedRelTypes}
              onChange={handleRelTypeFilter}
              style={{ minWidth: 180 }}
              maxTagCount={2}
              options={availableRelTypes.map(type => ({ value: type, label: type }))}
            />
          </div>

          {/* 搜索结果 */}
          {searchResults.length > 0 && (
            <div className="mb-4 p-2 bg-gray-50 rounded max-h-32 overflow-auto">
              <div className="text-xs text-gray-500 mb-2">
                找到 {searchResults.length} 个匹配节点:
              </div>
              <div className="flex flex-wrap gap-2">
                {searchResults.map(node => (
                  <Tag
                    key={node.id}
                    color={COLOR_MAP[node.nodeType]}
                    className="cursor-pointer"
                    onClick={() => focusNode(node.id)}
                  >
                    {node.label}
                  </Tag>
                ))}
              </div>
            </div>
          )}

          {/* 图例 */}
          <div className="flex gap-4 mb-4 text-sm">
            {Object.entries(NODE_TYPE_NAMES).map(([type, name]) => (
              <span 
                key={type}
                className={`flex items-center gap-1 cursor-pointer ${
                  selectedNodeTypes.includes(type) ? '' : 'opacity-40'
                }`}
                onClick={() => {
                  if (selectedNodeTypes.includes(type)) {
                    handleNodeTypeFilter(selectedNodeTypes.filter(t => t !== type))
                  } else {
                    handleNodeTypeFilter([...selectedNodeTypes, type])
                  }
                }}
              >
                <span 
                  className="inline-block w-3 h-3 rounded" 
                  style={{ backgroundColor: COLOR_MAP[type] }} 
                />
                {name}
              </span>
            ))}
          </div>

          {/* 图谱容器 */}
          {loading ? (
            <div className="flex justify-center items-center h-[600px]">
              <Spin size="large" />
            </div>
          ) : (
            <div ref={containerRef} style={{ height: 600 }} />
          )}
        </Card>
      </div>

      {/* 节点详情抽屉 */}
      <Drawer
        title={
          <div className="flex items-center gap-2">
            <span 
              className="inline-block w-4 h-4 rounded" 
              style={{ backgroundColor: selectedNode ? COLOR_MAP[selectedNode.nodeType] : '#666' }} 
            />
            <span>节点详情</span>
          </div>
        }
        placement="right"
        width={400}
        open={detailVisible}
        onClose={() => {
          setDetailVisible(false)
          graphRef.current?.getNodes().forEach(n => {
            graphRef.current?.clearItemStates(n, ['selected'])
          })
        }}
        closeIcon={<CloseOutlined />}
      >
        {selectedNode ? (
          <div className="space-y-4">
            {/* 基本信息 */}
            <Descriptions column={1} bordered size="small">
              <Descriptions.Item label="节点ID">{selectedNode.id}</Descriptions.Item>
              <Descriptions.Item label="节点名称">{selectedNode.label}</Descriptions.Item>
              <Descriptions.Item label="节点类型">
                <Tag color={COLOR_MAP[selectedNode.nodeType]}>
                  {NODE_TYPE_NAMES[selectedNode.nodeType] || selectedNode.nodeType}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            {/* 属性详情 */}
            <div>
              <div className="font-medium mb-2 text-gray-600">属性详情</div>
              {Object.keys(selectedNode.properties).length > 0 ? (
                <Descriptions column={1} bordered size="small">
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
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
    </div>
  )
}
