/**
 * 3D知识图谱类型定义
 */

export interface Position3D {
  x: number
  y: number
  z: number
}

export interface NodeStyle {
  color: string
  size: number
  opacity: number
}

export interface Graph3DNode {
  id: string
  nodeType: 'Standard' | 'Skill' | 'Category' | 'Domain' | 'TimeSlice' | 'StandardSeries' | 'SkillFamily'
  label: string
  properties: Record<string, unknown>
  position: Position3D
  style: NodeStyle
}

export interface Graph3DEdge {
  source: string
  target: string
  type: string
  properties?: Record<string, unknown>
}

export interface TimeSliceInfo {
  year: number
  z_position: number
  label: string
}

export interface DomainInfo {
  domain_id: string
  domain_name: string
  color: string
  sector_angle: number
}

export interface GraphMetadata {
  totalNodes: number
  totalEdges: number
  timeRange: {
    min: number | null
    max: number | null
  }
  domainCount: number
}

export interface Graph3DData {
  nodes: Graph3DNode[]
  edges: Graph3DEdge[]
  timeSlices: TimeSliceInfo[]
  domains: DomainInfo[]
  metadata: GraphMetadata
}

export interface Graph3DFilterParams {
  startYear?: number
  endYear?: number
  domains?: string[]
  limit?: number
}

// 节点类型颜色配置
export const NODE_COLORS: Record<string, string> = {
  Standard: '#00d4ff',
  Skill: '#ff6b6b',
  Category: '#7c3aed',
  Domain: '#f59e0b',
  TimeSlice: '#6366f1',
  StandardSeries: '#fbbf24',  // 金色 - 标准系列
  SkillFamily: '#34d399'      // 绿色 - 技能族
}

// 节点类型中文名
export const NODE_TYPE_NAMES: Record<string, string> = {
  Standard: '国标',
  Skill: '技能',
  Category: '类目',
  Domain: '领域',
  TimeSlice: '时间',
  StandardSeries: '系列',
  SkillFamily: '技能族'
}
