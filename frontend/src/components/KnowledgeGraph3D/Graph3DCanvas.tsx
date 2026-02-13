/**
 * 3D图谱画布组件
 * 使用3d-force-graph内置渲染，不直接导入Three.js避免双实例问题
 */
import { useEffect, useRef } from 'react'
import ForceGraph3D from '3d-force-graph'
import type { Graph3DData, Graph3DNode } from './types'

interface Graph3DCanvasProps {
  data: Graph3DData | null
  onNodeClick?: (node: Graph3DNode) => void
  onNodeHover?: (node: Graph3DNode | null) => void
  height?: number
}

// 节点类型颜色（高饱和度）
const COLORS: Record<string, string> = {
  Standard: '#00d4ff',
  Skill: '#ff6b6b',
  Category: '#a855f7',
  Domain: '#f59e0b',
  TimeSlice: '#6366f1'
}

// 节点类型中文名
const TYPE_NAMES: Record<string, string> = {
  Standard: '国标',
  Skill: '技能',
  Category: '类目',
  Domain: '领域',
  TimeSlice: '时间'
}

export default function Graph3DCanvas({
  data,
  onNodeClick,
  onNodeHover,
  height = 600
}: Graph3DCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<any>(null)
  const onNodeClickRef = useRef(onNodeClick)
  const onNodeHoverRef = useRef(onNodeHover)
  onNodeClickRef.current = onNodeClick
  onNodeHoverRef.current = onNodeHover

  // 初始化图谱
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const rect = container.getBoundingClientRect()
    const w = Math.max(rect.width, 400)
    const h = height

    const graph = ForceGraph3D()(container)
      .width(w)
      .height(h)
      .backgroundColor('#060a14')
      .showNavInfo(false)
      // 节点配置
      .nodeId('id')
      .nodeLabel((node: any) => {
        const typeName = TYPE_NAMES[node.nodeType] || node.nodeType
        const color = COLORS[node.nodeType] || '#666'
        return `<div style="background:rgba(6,10,20,0.9);padding:8px 12px;border-radius:8px;border:1px solid ${color};font-size:13px;color:#e0e0e0;text-align:center;min-width:80px">
          <div style="font-weight:bold;margin-bottom:3px">${node.label}</div>
          <div style="color:${color};font-size:11px">${typeName}</div>
        </div>`
      })
      .nodeColor((node: any) => COLORS[node.nodeType] || '#666')
      .nodeVal((node: any) => {
        // 增大节点尺寸以提高可见度
        const sizes: Record<string, number> = {
          Domain: 60,
          Standard: 35,
          Skill: 30,
          Category: 20,
          TimeSlice: 15
        }
        return sizes[node.nodeType] || 20
      })
      .nodeOpacity(0.95)
      .nodeResolution(20)
      // 边配置
      .linkSource('source')
      .linkTarget('target')
      .linkColor((link: any) => {
        const colors: Record<string, string> = {
          'BELONGS_TO': 'rgba(0, 212, 255, 0.35)',
          'DERIVED_FROM': 'rgba(255, 107, 107, 0.35)',
          'CHILD_OF': 'rgba(168, 85, 247, 0.3)',
        }
        return colors[link.type] || 'rgba(100, 140, 200, 0.3)'
      })
      .linkWidth(1.2)
      .linkOpacity(0.7)
      .linkDirectionalArrowLength(4)
      .linkDirectionalArrowRelPos(1)
      .linkDirectionalArrowColor((link: any) => {
        const colors: Record<string, string> = {
          'BELONGS_TO': '#00d4ff',
          'DERIVED_FROM': '#ff6b6b',
          'CHILD_OF': '#a855f7',
        }
        return colors[link.type] || '#648cb8'
      })
      // 流动粒子 - 科技感
      .linkDirectionalParticles(2)
      .linkDirectionalParticleWidth(1.8)
      .linkDirectionalParticleSpeed(0.004)
      .linkDirectionalParticleColor((link: any) => {
        return link.type === 'BELONGS_TO' ? '#00d4ff' :
               link.type === 'DERIVED_FROM' ? '#ff6b6b' : '#648cb8'
      })
      // 交互
      .onNodeClick((node: any) => {
        onNodeClickRef.current?.(node as Graph3DNode)
      })
      .onNodeHover((node: any) => {
        onNodeHoverRef.current?.(node as Graph3DNode | null)
        if (container) {
          container.style.cursor = node ? 'pointer' : 'default'
        }
      })
      // 力导向
      .d3AlphaDecay(0.02)
      .d3VelocityDecay(0.3)

    graphRef.current = graph

    return () => {
      if (graphRef.current) {
        graphRef.current._destructor?.()
        graphRef.current = null
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 尺寸变化
  useEffect(() => {
    if (!graphRef.current || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const w = Math.max(rect.width, 400)
    graphRef.current.width(w).height(height)
  }, [height])

  // 监听容器宽度变化
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.floor(entry.contentRect.width)
        if (w > 0 && graphRef.current) {
          graphRef.current.width(w)
        }
      }
    })
    observer.observe(container)
    return () => observer.disconnect()
  }, [])

  // 更新数据
  useEffect(() => {
    if (!graphRef.current || !data) return

    const graphData = {
      nodes: data.nodes.map(node => ({
        ...node,
        fx: node.position.x,
        fy: node.position.y,
        fz: node.position.z,
        x: node.position.x,
        y: node.position.y,
        z: node.position.z
      })),
      links: data.edges.map(edge => ({
        source: edge.source,
        target: edge.target,
        type: edge.type
      }))
    }

    graphRef.current.graphData(graphData)

    setTimeout(() => {
      if (graphRef.current) {
        graphRef.current.zoomToFit(800, 80)
      }
    }, 600)
  }, [data])

  return (
    <div 
      ref={containerRef} 
      style={{ 
        width: '100%', 
        height: `${height}px`,
        background: '#060a14',
        borderRadius: '8px',
        overflow: 'hidden',
        position: 'relative'
      }}
    />
  )
}
