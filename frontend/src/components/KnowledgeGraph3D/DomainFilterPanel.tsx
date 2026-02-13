/**
 * 领域过滤面板组件
 */
import { Checkbox, Space, Typography, Button } from 'antd'
import type { DomainInfo } from './types'

const { Text } = Typography

interface DomainFilterPanelProps {
  domains: DomainInfo[]
  selectedDomains: string[]
  onChange?: (domains: string[]) => void
}

export default function DomainFilterPanel({
  domains,
  selectedDomains,
  onChange
}: DomainFilterPanelProps) {
  const allSelected = selectedDomains.length === domains.length
  const indeterminate = selectedDomains.length > 0 && selectedDomains.length < domains.length

  const handleSelectAll = () => {
    if (allSelected) {
      onChange?.([])
    } else {
      onChange?.(domains.map(d => d.domain_id))
    }
  }

  const handleToggle = (domainId: string) => {
    if (selectedDomains.includes(domainId)) {
      onChange?.(selectedDomains.filter(id => id !== domainId))
    } else {
      onChange?.([...selectedDomains, domainId])
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <Text className="text-gray-300 text-sm font-medium">领域筛选</Text>
        <Button 
          type="link" 
          size="small" 
          onClick={handleSelectAll}
          className="text-cyan-400 p-0"
        >
          {allSelected ? '取消全选' : '全选'}
        </Button>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {domains.map(domain => (
          <div 
            key={domain.domain_id}
            className="flex items-center gap-2 cursor-pointer hover:bg-gray-700 rounded px-2 py-1"
            onClick={() => handleToggle(domain.domain_id)}
          >
            <Checkbox 
              checked={selectedDomains.includes(domain.domain_id)}
              onChange={() => handleToggle(domain.domain_id)}
            />
            <span 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: domain.color }}
            />
            <Text className="text-gray-300 text-sm">{domain.domain_name}</Text>
          </div>
        ))}
      </div>
      
      {domains.length === 0 && (
        <div className="text-gray-500 text-sm text-center py-4">
          暂无领域数据
        </div>
      )}
    </div>
  )
}
