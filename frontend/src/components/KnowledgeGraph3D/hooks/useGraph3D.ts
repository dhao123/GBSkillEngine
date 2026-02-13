/**
 * 3D知识图谱数据Hook
 */
import { useState, useCallback, useEffect } from 'react'
import { message } from 'antd'
import { knowledgeGraphApi } from '@/services/api'
import type { Graph3DData, Graph3DFilterParams, DomainInfo, TimeSliceInfo } from '../types'

export function useGraph3D() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<Graph3DData | null>(null)
  const [domains, setDomains] = useState<DomainInfo[]>([])
  const [timeSlices, setTimeSlices] = useState<TimeSliceInfo[]>([])
  const [filters, setFilters] = useState<Graph3DFilterParams>({})

  // 加载图谱数据
  const loadGraphData = useCallback(async (params?: Graph3DFilterParams) => {
    setLoading(true)
    try {
      const queryParams: Record<string, unknown> = {}
      
      if (params?.startYear) queryParams.start_year = params.startYear
      if (params?.endYear) queryParams.end_year = params.endYear
      if (params?.domains?.length) queryParams.domains = params.domains.join(',')
      if (params?.limit) queryParams.limit = params.limit

      const result = await knowledgeGraphApi.visualize3D<Graph3DData>(queryParams)
      setData(result)
    } catch (error) {
      console.error('加载3D图谱数据失败:', error)
      message.error('加载3D图谱数据失败')
    } finally {
      setLoading(false)
    }
  }, [])

  // 加载领域列表
  const loadDomains = useCallback(async () => {
    try {
      const result = await knowledgeGraphApi.getDomains<DomainInfo[]>()
      setDomains(result)
    } catch (error) {
      console.error('加载领域列表失败:', error)
    }
  }, [])

  // 加载时间切片列表
  const loadTimeSlices = useCallback(async () => {
    try {
      const result = await knowledgeGraphApi.getTimeSlices<TimeSliceInfo[]>()
      setTimeSlices(result)
    } catch (error) {
      console.error('加载时间切片失败:', error)
    }
  }, [])

  // 更新过滤条件
  const updateFilters = useCallback((newFilters: Partial<Graph3DFilterParams>) => {
    setFilters(prev => {
      const updated = { ...prev, ...newFilters }
      loadGraphData(updated)
      return updated
    })
  }, [loadGraphData])

  // 刷新数据
  const refresh = useCallback(() => {
    loadGraphData(filters)
  }, [loadGraphData, filters])

  // 初始加载
  useEffect(() => {
    Promise.all([
      loadGraphData(),
      loadDomains(),
      loadTimeSlices()
    ])
  }, [loadGraphData, loadDomains, loadTimeSlices])

  return {
    loading,
    data,
    domains,
    timeSlices,
    filters,
    updateFilters,
    refresh
  }
}
