/**
 * 3D知识图谱主组件
 */
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import { Card, Spin, Button, Space, Statistic, Row, Col } from 'antd'
import { ReloadOutlined, FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons'
import Graph3DCanvas from './Graph3DCanvas'
import TimeAxisController from './TimeAxisController'
import DomainFilterPanel from './DomainFilterPanel'
import NodeDetailPanel from './NodeDetailPanel'
import { useGraph3D } from './hooks/useGraph3D'
import type { Graph3DNode, Graph3DData } from './types'

export default function KnowledgeGraph3D() {
  const { loading, data, domains, timeSlices, filters, updateFilters, refresh } = useGraph3D()
  
  // 选中的节点
  const [selectedNode, setSelectedNode] = useState<Graph3DNode | null>(null)
  const [detailVisible, setDetailVisible] = useState(false)
  
  // 选中的领域
  const [selectedDomains, setSelectedDomains] = useState<string[]>([])
  
  // 时间范围
  const [timeRange, setTimeRange] = useState<[number, number] | undefined>()
  
  // 全屏状态
  const [isFullscreen, setIsFullscreen] = useState(false)

  // 标记领域是否已初始化，防止清空时被重新全选
  const domainsInitialized = useRef(false)

  // 初始化选中所有领域（仅首次加载）
  useEffect(() => {
    if (domains.length > 0 && !domainsInitialized.current) {
      setSelectedDomains(domains.map(d => d.domain_id))
      domainsInitialized.current = true
    }
  }, [domains])

  // 初始化时间范围
  useEffect(() => {
    if (timeSlices.length > 0 && !timeRange) {
      const years = timeSlices.map(t => t.year).sort((a, b) => a - b)
      setTimeRange([years[0], years[years.length - 1]])
    }
  }, [timeSlices, timeRange])

  // 节点点击处理
  const handleNodeClick = useCallback((node: Graph3DNode) => {
    setSelectedNode(node)
    setDetailVisible(true)
  }, [])

  // 领域过滤变更 - 仅更新本地状态，由filteredData进行客户端过滤
  const handleDomainChange = useCallback((domains: string[]) => {
    setSelectedDomains(domains)
  }, [])

  // 时间范围变更
  const handleTimeRangeChange = useCallback((range: [number, number]) => {
    setTimeRange(range)
    updateFilters({ startYear: range[0], endYear: range[1] })
  }, [updateFilters])

  // 切换全屏
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev)
  }, [])

  // 按选中领域进行客户端过滤
  const filteredData = useMemo((): Graph3DData | null => {
    if (!data) return null

    // 全选或未初始化时直接返回原数据
    if (selectedDomains.length === domains.length && domains.length > 0) return data

    // 过滤节点：Domain节点按ID匹配，其他节点按properties.domain匹配
    const filteredNodes = data.nodes.filter(node => {
      if (node.nodeType === 'Domain') {
        return selectedDomains.includes(node.id)
      }
      if (node.nodeType === 'TimeSlice') {
        return true // 时间切片始终保留
      }
      const nodeDomain = node.properties?.domain as string | undefined
      if (!nodeDomain) return false
      return selectedDomains.includes(`domain_${nodeDomain}`)
    })

    // 构建存活节点ID集合，用于过滤边
    const nodeIds = new Set(filteredNodes.map(n => n.id))
    const filteredEdges = data.edges.filter(
      edge => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    )

    return {
      ...data,
      nodes: filteredNodes,
      edges: filteredEdges,
      metadata: {
        ...data.metadata,
        totalNodes: filteredNodes.length,
        totalEdges: filteredEdges.length
      }
    }
  }, [data, selectedDomains, domains.length])

  // 统计数据（基于过滤后的数据）
  const stats = useMemo(() => {
    if (!filteredData) return { nodes: 0, edges: 0, standards: 0, skills: 0 }
    return {
      nodes: filteredData.metadata.totalNodes,
      edges: filteredData.metadata.totalEdges,
      standards: filteredData.nodes.filter(n => n.nodeType === 'Standard').length,
      skills: filteredData.nodes.filter(n => n.nodeType === 'Skill').length
    }
  }, [filteredData])

  return (
    <div className={`flex flex-col gap-4 ${isFullscreen ? 'fixed inset-0 z-50 bg-gray-900 p-4' : ''}`}>
      {/* 标题栏 */}
      <Card 
        size="small"
        className="bg-gray-900 border-gray-700"
        styles={{ body: { padding: '12px 16px' } }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-lg font-bold text-white">3D MRO知识图谱</span>
            <Row gutter={24}>
              <Col>
                <Statistic 
                  title={<span className="text-gray-400 text-xs">节点</span>} 
                  value={stats.nodes} 
                  valueStyle={{ color: '#00d4ff', fontSize: 16 }}
                />
              </Col>
              <Col>
                <Statistic 
                  title={<span className="text-gray-400 text-xs">关系</span>} 
                  value={stats.edges} 
                  valueStyle={{ color: '#10b981', fontSize: 16 }}
                />
              </Col>
              <Col>
                <Statistic 
                  title={<span className="text-gray-400 text-xs">国标</span>} 
                  value={stats.standards} 
                  valueStyle={{ color: '#00d4ff', fontSize: 16 }}
                />
              </Col>
              <Col>
                <Statistic 
                  title={<span className="text-gray-400 text-xs">技能</span>} 
                  value={stats.skills} 
                  valueStyle={{ color: '#ff6b6b', fontSize: 16 }}
                />
              </Col>
            </Row>
          </div>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={refresh}
              loading={loading}
            >
              刷新
            </Button>
            <Button 
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={toggleFullscreen}
            >
              {isFullscreen ? '退出全屏' : '全屏'}
            </Button>
          </Space>
        </div>
      </Card>

      {/* 主内容区 */}
      <div className="flex gap-4 flex-1" style={{ minHeight: isFullscreen ? 'calc(100vh - 180px)' : '600px' }}>
        {/* 左侧过滤面板 */}
        <div className="w-48 flex flex-col gap-4">
          <DomainFilterPanel
            domains={domains}
            selectedDomains={selectedDomains}
            onChange={handleDomainChange}
          />
        </div>

        {/* 中间3D图谱 */}
        <div className="flex-1 bg-gray-900 rounded-lg overflow-hidden relative">
          <Graph3DCanvas
            data={filteredData}
            onNodeClick={handleNodeClick}
            height={isFullscreen ? window.innerHeight - 200 : 600}
          />
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-70 z-10">
              <Spin size="large" />
            </div>
          )}
          
          {/* 图例 */}
          <div className="absolute bottom-4 left-4 bg-gray-800 bg-opacity-80 rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2">图例</div>
            <div className="flex flex-wrap gap-3">
              {[
                { type: 'Standard', name: '国标', color: '#00d4ff' },
                { type: 'Skill', name: '技能', color: '#ff6b6b' },
                { type: 'Category', name: '类目', color: '#7c3aed' },
                { type: 'Domain', name: '领域', color: '#f59e0b' },
              ].map(item => (
                <div key={item.type} className="flex items-center gap-1">
                  <span 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-xs text-gray-300">{item.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 操作提示 */}
          <div className="absolute top-4 right-4 bg-gray-800 bg-opacity-80 rounded-lg p-2 text-xs text-gray-400">
            <div>鼠标左键拖动: 旋转</div>
            <div>鼠标右键拖动: 平移</div>
            <div>滚轮: 缩放</div>
            <div>点击节点: 查看详情</div>
          </div>
        </div>
      </div>

      {/* 底部时间轴 */}
      <TimeAxisController
        timeSlices={timeSlices}
        value={timeRange}
        onChange={handleTimeRangeChange}
      />

      {/* 节点详情面板 */}
      <NodeDetailPanel
        visible={detailVisible}
        node={selectedNode}
        onClose={() => {
          setDetailVisible(false)
          setSelectedNode(null)
        }}
      />
    </div>
  )
}

export { Graph3DCanvas, TimeAxisController, DomainFilterPanel, NodeDetailPanel }
export * from './types'
