import type { GetProp, TableProps } from 'antd';
import { Table } from 'antd';
import { getSpinPros } from '@/constants/spin';

type ColumnsType<T extends object> = GetProp<TableProps<T>, 'columns'>;

interface EnhancedTableProps<T extends object> extends TableProps<T> {
  bordered?: boolean;
  columns: ColumnsType<T>;
  dataSource?: T[];
  ellipsis?: boolean;
  loading?: boolean;
  pagination?: TableProps<T>['pagination'];
  rowKey?: ((record: T) => string) | string;
  rowSelection?: TableRowSelection<T>;
  size?: 'large' | 'middle' | 'small';
  xScroll?: string;
}

type TableRowSelection<T extends object> = TableProps<T>['rowSelection'];

/**
 * BaseTable - 统一表格组件
 * 
 * 为了统一table的风格(是否加载，size,是否展示border边框，分页等），重新封装一遍table组件
 * 非特殊table都尽量引用这个组件
 * 
 * @example
 * ```tsx
 * <BaseTable
 *   columns={columns}
 *   dataSource={data}
 *   loading={loading}
 *   pagination={{
 *     current: page,
 *     pageSize: pageSize,
 *     total: total,
 *     onChange: handlePageChange
 *   }}
 *   rowKey="id"
 * />
 * ```
 */
function BaseTable<T extends object>({
  bordered = false, // 是否显示边框
  columns,
  dataSource,
  ellipsis = true, // 是否显示省略号
  loading = true,
  pagination,
  rowKey = 'id', // 表格行数据的 key
  rowSelection, // 是否有行选择框
  size = 'large',
  xScroll = 'max-content', // 横向滚动条
  ...otherProps
}: EnhancedTableProps<T>) {
  const scroll: { x?: number | string; y?: number | string } = {
    x: xScroll,
  };

  const tableColumns = columns.map((item) => {
    item.align ??= 'center';
    return { ...item, ellipsis };
  }) as unknown as ColumnsType<T>;

  const tableProps: TableProps = {
    bordered: bordered,
    pagination: {
      showQuickJumper: true, // 是否显示快速跳转
      showSizeChanger: true, // 是否显示每页显示多少条数据
      showTotal: (total) => `总共 ${total.toString()} 条`, // 显示总条数
      ...pagination,
    },
    rowKey,
    rowSelection,
    scroll,
    size,
  };

  return (
    <Table
      {...otherProps}
      {...tableProps}
      columns={tableColumns}
      dataSource={dataSource ?? []}
      loading={getSpinPros(loading)}
      scroll={scroll}
    />
  );
}

export default BaseTable;
