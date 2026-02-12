import { useEffect, useState, useRef } from 'react'
import { Card, Spin, message } from 'antd'
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

export default function KnowledgeGraph() {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<InstanceType<typeof G6.Graph> | null>(null)
  const [loading, setLoading] = useState(true)

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
      renderGraph(res)
    } catch (error) {
      message.error('加载知识图谱失败')
    } finally {
      setLoading(false)
    }
  }

  const renderGraph = (data: GraphData) => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.scrollWidth
    const height = container.scrollHeight || 600

    // 节点颜色映射
    const colorMap: Record<string, string> = {
      Standard: '#3462FE',
      Category: '#9D34FE',
      Attribute: '#52c41a',
      DimensionTable: '#faad14',
      Material: '#1890ff',
      MaterialInstance: '#13c2c2',
    }

    // 转换数据格式
    const nodes = data.nodes.map((node) => ({
      id: node.id,
      label: node.properties.standardCode || node.properties.categoryName || 
             node.properties.attributeName || node.label,
      nodeType: node.label,
      style: {
        fill: colorMap[node.label] || '#666',
      },
    }))

    const edges = data.edges.map((edge) => ({
      source: edge.source,
      target: edge.target,
      label: edge.type,
    }))

    graphRef.current = new G6.Graph({
      container,
      width,
      height,
      fitView: true,
      fitViewPadding: 50,
      layout: {
        type: 'force',
        preventOverlap: true,
        nodeSpacing: 80,
        linkDistance: 150,
      },
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
    })

    graphRef.current.data({ nodes, edges })
    graphRef.current.render()

    // 节点点击事件
    graphRef.current.on('node:click', (evt) => {
      const node = evt.item?.getModel()
      if (node) {
        message.info(`节点: ${node.label} (${node.nodeType})`)
      }
    })
  }

  return (
    <div className="space-y-4">
      <Card
        title="MRO国标知识图谱"
        extra={
          <div className="flex gap-4 text-sm">
            <span><span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: '#3462FE' }} /> 标准</span>
            <span><span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: '#9D34FE' }} /> 类目</span>
            <span><span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: '#52c41a' }} /> 属性</span>
            <span><span className="inline-block w-3 h-3 rounded" style={{ backgroundColor: '#faad14' }} /> 尺寸表</span>
          </div>
        }
      >
        {loading ? (
          <div className="flex justify-center items-center h-[600px]">
            <Spin size="large" />
          </div>
        ) : (
          <div ref={containerRef} style={{ height: 600 }} />
        )}
      </Card>
    </div>
  )
}
