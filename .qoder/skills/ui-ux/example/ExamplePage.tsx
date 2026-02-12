import Layout from './components/Layout';
import Banner from './components/Banner';
import BaseTable from './components/BaseTable';
import Tag from './components/Tag';

// 示例数据
const sampleData = [
  { id: 1, name: '模型A', type: '语言模型', status: '在线', created: '2024-01-01' },
  { id: 2, name: '模型B', type: '视觉模型', status: '离线', created: '2024-01-02' },
  { id: 3, name: '模型C', type: '多模态', status: '在线', created: '2024-01-03' },
];

const columns = [
  {
    title: '模型名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '模型类型',
    dataIndex: 'type',
    key: 'type',
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    render: (status: string) => (
      <Tag name={status} id={1} />
    ),
  },
  {
    title: '创建时间',
    dataIndex: 'created',
    key: 'created',
  },
  {
    title: '操作',
    key: 'action',
    render: () => (
      <span>
        <a>编辑</a>
        <span className="mx-2">|</span>
        <a className="text-red-500">删除</a>
      </span>
    ),
  },
];

// 示例菜单
const menuList = [
  {
    name: '开发',
    children: [
      { name: '模型', icon: 'icon-moxing', link: '/model' },
      { name: '应用', icon: 'icon-yingyong', link: '/application' },
      { name: '知识库', icon: 'icon-zhishiku', link: '/knowledge' },
    ]
  },
  {
    name: '评测',
    children: [
      { name: '评测中心', icon: 'icon-pingce', link: '/testing' },
      { name: '维度管理', icon: 'icon-weidu', link: '/dimension' },
    ]
  }
];

// 示例用户
const user = {
  username: 'developer@example.com',
  nickname: '测试者',
};

// 示例页面
const ExamplePage = () => {
  return (
    <Layout
      mode="common"
      navProps={{ menuList }}
      headerProps={{ 
        user, 
        isLogin: true,
        headerMenu: [
          { icon: 'zkh:ai-dev:rili', link: 'https://aidev-docs.zkh360.com', title: '产品文档' },
        ]
      }}
    >
      <Banner type="model" />
      
      <div className="mt-6 bg-white p-6 rounded-lg">
        <h2 className="text-xl font-bold mb-4">模型列表</h2>
        <BaseTable
          columns={columns}
          dataSource={sampleData}
          rowKey="id"
          pagination={{ 
            current: 1, 
            pageSize: 10, 
            total: sampleData.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </div>
    </Layout>
  );
};

export default ExamplePage;
