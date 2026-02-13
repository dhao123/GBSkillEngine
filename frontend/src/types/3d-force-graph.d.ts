/**
 * 3d-force-graph 类型声明
 */
declare module '3d-force-graph' {
  import { Scene, Camera, WebGLRenderer, Object3D } from 'three'

  interface GraphNode {
    id?: string | number
    x?: number
    y?: number
    z?: number
    fx?: number
    fy?: number
    fz?: number
    vx?: number
    vy?: number
    vz?: number
    [key: string]: unknown
  }

  interface GraphLink {
    source: string | number | GraphNode
    target: string | number | GraphNode
    [key: string]: unknown
  }

  interface GraphData {
    nodes: GraphNode[]
    links: GraphLink[]
  }

  type NodeAccessor<T> = T | ((node: GraphNode) => T)
  type LinkAccessor<T> = T | ((link: GraphLink) => T)

  interface ForceGraph3DInstance {
    // Data
    graphData(data?: GraphData): ForceGraph3DInstance & GraphData
    
    // Container
    width(width?: number): ForceGraph3DInstance & number
    height(height?: number): ForceGraph3DInstance & number
    backgroundColor(color?: string): ForceGraph3DInstance & string
    
    // Nodes
    nodeId(accessor?: NodeAccessor<string>): ForceGraph3DInstance
    nodeLabel(accessor?: NodeAccessor<string>): ForceGraph3DInstance
    nodeColor(accessor?: NodeAccessor<string>): ForceGraph3DInstance
    nodeVal(accessor?: NodeAccessor<number>): ForceGraph3DInstance
    nodeOpacity(opacity?: number): ForceGraph3DInstance & number
    nodeThreeObject(obj?: NodeAccessor<Object3D | null>): ForceGraph3DInstance
    nodeThreeObjectExtend(extend?: boolean): ForceGraph3DInstance
    
    // Links
    linkSource(accessor?: string): ForceGraph3DInstance
    linkTarget(accessor?: string): ForceGraph3DInstance
    linkColor(accessor?: LinkAccessor<string>): ForceGraph3DInstance
    linkWidth(accessor?: LinkAccessor<number>): ForceGraph3DInstance
    linkOpacity(opacity?: number): ForceGraph3DInstance & number
    linkDirectionalArrowLength(length?: LinkAccessor<number>): ForceGraph3DInstance & number
    linkDirectionalArrowRelPos(pos?: number): ForceGraph3DInstance & number
    linkDirectionalArrowColor(accessor?: LinkAccessor<string>): ForceGraph3DInstance
    linkDirectionalParticles(num?: LinkAccessor<number>): ForceGraph3DInstance
    linkDirectionalParticleWidth(width?: LinkAccessor<number>): ForceGraph3DInstance
    linkDirectionalParticleSpeed(speed?: LinkAccessor<number>): ForceGraph3DInstance
    linkDirectionalParticleColor(accessor?: LinkAccessor<string>): ForceGraph3DInstance
    
    // Interaction
    onNodeClick(callback?: (node: GraphNode, event: MouseEvent) => void): ForceGraph3DInstance
    onNodeHover(callback?: (node: GraphNode | null, prevNode: GraphNode | null) => void): ForceGraph3DInstance
    onLinkClick(callback?: (link: GraphLink, event: MouseEvent) => void): ForceGraph3DInstance
    
    // Force engine
    d3AlphaDecay(decay?: number): ForceGraph3DInstance & number
    d3VelocityDecay(decay?: number): ForceGraph3DInstance & number
    d3Force(forceName: string): unknown
    
    // Camera
    cameraPosition(position?: { x?: number; y?: number; z?: number }, lookAt?: { x?: number; y?: number; z?: number }, transitionDuration?: number): ForceGraph3DInstance
    zoomToFit(duration?: number, padding?: number): ForceGraph3DInstance
    
    // Three.js access
    scene(): Scene
    camera(): Camera
    renderer(): WebGLRenderer
    
    // Lifecycle
    _destructor?(): void
  }

  function ForceGraph3D(): (element: HTMLElement) => ForceGraph3DInstance

  export default ForceGraph3D
}
