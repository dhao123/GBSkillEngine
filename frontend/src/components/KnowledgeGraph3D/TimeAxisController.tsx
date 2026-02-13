/**
 * 时间轴控制器组件
 */
import { useMemo } from 'react'
import { Slider, Space, Typography } from 'antd'
import type { TimeSliceInfo } from './types'

const { Text } = Typography

interface TimeAxisControllerProps {
  timeSlices: TimeSliceInfo[]
  value?: [number, number]
  onChange?: (range: [number, number]) => void
}

export default function TimeAxisController({
  timeSlices,
  value,
  onChange
}: TimeAxisControllerProps) {
  // 计算时间范围
  const { min, max, marks } = useMemo(() => {
    if (!timeSlices.length) {
      return { min: 2018, max: 2024, marks: {} }
    }
    
    const years = timeSlices.map(t => t.year).sort((a, b) => a - b)
    const minYear = years[0]
    const maxYear = years[years.length - 1]
    
    // 生成刻度标记
    const marks: Record<number, string> = {}
    years.forEach(year => {
      marks[year] = `${year}`
    })
    
    return { min: minYear, max: maxYear, marks }
  }, [timeSlices])

  const currentValue = value || [min, max]

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <Text className="text-gray-300 text-sm">时间范围</Text>
        <Text className="text-cyan-400 text-sm">
          {currentValue[0]} - {currentValue[1]}
        </Text>
      </div>
      <Slider
        range
        min={min}
        max={max}
        marks={marks}
        value={currentValue}
        onChange={(val) => onChange?.(val as [number, number])}
        tooltip={{ formatter: (val) => `${val}年` }}
        styles={{
          track: { background: '#00d4ff' },
          rail: { background: '#374151' }
        }}
      />
    </div>
  )
}
