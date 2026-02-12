import { Table, Spin } from 'antd'
import type { TableProps } from 'antd'

interface BaseTableProps<T> extends TableProps<T> {
  loading?: boolean
}

export default function BaseTable<T extends object>({
  loading = false,
  columns,
  dataSource,
  pagination,
  ...rest
}: BaseTableProps<T>) {
  const enhancedColumns = columns?.map((col) => ({
    ...col,
    align: col.align || 'center' as const,
    ellipsis: col.ellipsis !== false,
  }))

  return (
    <Spin spinning={loading}>
      <Table<T>
        columns={enhancedColumns}
        dataSource={dataSource}
        pagination={
          pagination === false
            ? false
            : {
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条`,
                ...pagination,
              }
        }
        bordered={false}
        size="middle"
        {...rest}
      />
    </Spin>
  )
}
