/**
 * WorkSpaceSelect - 工作空间选择器组件
 * 支持工作空间切换、申请加入空间、创建新空间
 * 
 * @usage
 * ```tsx
 * <WorkSpaceSelect defaultWorkSpace={user?.defaultWorkSpace} />
 * ```
 */
import type { FormProps } from 'antd';

import { CaretDownOutlined } from '@ant-design/icons';
import { Icon } from '@iconify/react';
import { Button, ConfigProvider, Divider, Form, Input, message, Modal, Select, Spin } from 'antd';
import { useEffect, useState } from 'react';

import { getSpinIndicator } from '../constants/spin';
import { Channel } from '../utils/channel';
import request from '../utils/request';

export interface WorkSpaceItem {
  id: number;
  name: string;
  perm?: number; // 1 管理员、2 成员
  permName?: string;
}

interface FieldType {
  remark?: string;
  tenantId?: number;
}

interface WorkSpaceForm {
  name: string;
  reason: string;
  remark?: string;
}

// 获取工作空间列表
const fetchWorkSpaceList = async () => {
  const workSpace = await request<WorkSpaceItem[]>('/api-dev/backend/sys/user/tenants', {
    method: 'GET',
  });
  return workSpace;
};

// 切换默认工作空间
const changeDefaultWorkSpace = async (tenantId: number) => {
  const defaultWorkSpace = await request<WorkSpaceItem>(
    '/api-dev/backend/sys/user/tenant/set/def?tenantId=' + tenantId.toString(),
    {
      method: 'GET',
    },
  );
  return defaultWorkSpace;
};

const callback = () => {
  Modal.warning({
    content: '您已经切换工作空间，相关信息已经发生变化，请刷新页面重新获取信息！',
    okText: '确定刷新',
    onOk: () => {
      globalThis.location.reload();
    },
    title: '提示',
  });
};

const onFinishFailed: FormProps<FieldType>['onFinishFailed'] = (errorInfo) => {
  console.error('Failed:', errorInfo);
};

const instant = Channel.getInstance();
const action = 'workspace-change';

export default function WorkSpaceSelect({
  className,
  defaultWorkSpace,
  style,
}: {
  className?: string;
  defaultWorkSpace: null | WorkSpaceItem;
  style?: React.CSSProperties;
}) {
  const [workSpaceList, setWorkSpaceList] = useState<WorkSpaceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showDlg, setShowDlg] = useState<boolean>(false);
  const [showSpaceCreate, setShowSpaceCreate] = useState<boolean>(false);
  const [applyLoading, setApplyLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchWorkSpaceList()
      .then((data) => {
        setWorkSpaceList(data);
      })
      .catch((error: unknown) => {
        console.error('Error fetching workspaces:', error);
      })
      .finally(() => {
        setLoading(false);
      });
    instant.addAction(action, () => {
      callback();
    });
    return () => {
      instant.removeAction(action);
    };
  }, []);

  const handleChange = (value: number) => {
    setLoading(true);
    changeDefaultWorkSpace(value)
      .then(() => {
        instant.postMessage(action);
        globalThis.location.reload();
      })
      .catch((error: unknown) => {
        console.error('Error setting default workspace:', error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const onFinish: FormProps<FieldType>['onFinish'] = (values) => {
    setApplyLoading(true);
    request('/api-dev/backend/tenant/perm/apply', {
      body: {
        remark: values.remark,
        tenantId: values.tenantId?.toString(),
      },
      method: 'POST',
    })
      .then(() => {
        setShowDlg(false);
      })
      .catch((error: unknown) => {
        console.error('Error submitting application:', error);
      })
      .finally(() => {
        setApplyLoading(false);
      });
  };

  const onSpaceCreateFinish: FormProps<WorkSpaceForm>['onFinish'] = (values) => {
    setApplyLoading(true);
    request('/api-dev/backend/tenants/create/apply', {
      body: {
        name: values.name,
        reason: values.reason,
        remark: values.remark,
      },
      method: 'POST',
    })
      .then(() => {
        message.success('申请成功，待系统管理员处理');
        setShowSpaceCreate(false);
      })
      .catch((error: unknown) => {
        console.error('Error submitting application:', error);
      })
      .finally(() => {
        setApplyLoading(false);
      });
  };

  return (
    <>
      <ConfigProvider
        theme={{
          components: {
            Select: {
              optionPadding: '11px 12px',
            },
          },
        }}>
        <Select
          className={className}
          labelRender={(item) => {
            return (
              <span className="text-[14px] text-[#333]">
                工作空间:
                <span className="text-[#1F4CF0] font-semibold ml-[10px]">{item.label}</span>
              </span>
            );
          }}
          loading={loading}
          onChange={handleChange}
          optionRender={(option) => (
            <div className="flex items-center justify-between px-2">
              <span>{option.label}</span>
              <span className="text-gray-500 text-xs">{option.data.permname}</span>
            </div>
          )}
          options={workSpaceList.map((item) => ({
            label: item.name,
            permname: item.permName,
            value: item.id,
          }))}
          placeholder="请选择工作空间"
          popupRender={(items) => {
            return (
              <>
                {items}
                <Divider style={{ margin: '8px 0' }} />
                <div
                  className="h-[44px] px-2 flex items-center cursor-pointer hover:bg-[#F5F5F5]"
                  onClick={() => {
                    setShowDlg(true);
                  }}>
                  <Icon icon="zkh:ant-design:plus-outlined" />
                  <span className="ml-[4px]">创建或加入其他空间</span>
                </div>
              </>
            );
          }}
          style={style}
          suffix={<CaretDownOutlined style={{ color: '#1F4CF0' }} />}
          value={defaultWorkSpace?.id}
        />
      </ConfigProvider>
      {/* 申请加入空间弹窗 */}
      <Modal
        centered
        destroyOnHidden
        footer={null}
        onCancel={() => {
          setShowDlg(false);
        }}
        open={showDlg}
        title="申请加入空间"
        width={600}>
        <Spin indicator={getSpinIndicator()} spinning={applyLoading}>
          <Form
            autoComplete="off"
            initialValues={{ remember: true }}
            labelCol={{ span: 4 }}
            onFinish={onFinish}
            onFinishFailed={onFinishFailed}
            style={{ maxWidth: 600 }}
            wrapperCol={{ span: 20 }}>
            <Form.Item<FieldType>
              label="工作空间"
              name="tenantId"
              rules={[{ message: '请选择!', required: true }]}>
              <Select placeholder="请选择要加入的工作空间" />
            </Form.Item>

            <Form.Item<FieldType>
              label="备注"
              name="remark"
              rules={[{ message: '请输入!', required: true }]}>
              <Input.TextArea maxLength={50} placeholder="申请备注" showCount={true} />
            </Form.Item>
            <Form.Item label={null}>
              <div>tips: 申请后由空间负责人进行审核处理</div>
            </Form.Item>
            <Form.Item label={null}>
              <div className="flex items-center justify-center gap-4">
                <Button htmlType="submit" type="primary">
                  确认
                </Button>
                <Button
                  onClick={() => {
                    setShowDlg(false);
                    setShowSpaceCreate(true);
                  }}>
                  创建新工作空间
                </Button>
              </div>
            </Form.Item>
          </Form>
        </Spin>
      </Modal>
      {/* 创建工作空间弹窗 */}
      <Modal
        centered
        destroyOnHidden
        footer={null}
        onCancel={() => {
          setShowSpaceCreate(false);
        }}
        open={showSpaceCreate}
        title="申请创建工作空间"
        width={600}>
        <Spin indicator={getSpinIndicator()} spinning={applyLoading}>
          <Form<WorkSpaceForm>
            autoComplete="off"
            initialValues={{ remember: true }}
            labelCol={{ span: 4 }}
            onFinish={onSpaceCreateFinish}
            onFinishFailed={onFinishFailed}
            style={{ maxWidth: 600 }}
            wrapperCol={{ span: 20 }}>
            <Form.Item
              label="空间名称"
              name="name"
              rules={[{ message: '请输入空间名称!', required: true }]}>
              <Input
                maxLength={30}
                placeholder="唯一，不能重复，尽量用部门/团队/项目名称,如采购部"
                showCount={true}
              />
            </Form.Item>
            <Form.Item
              label="用途&背景"
              name="reason"
              rules={[{ message: '请输入!', required: true }]}>
              <Input.TextArea
                maxLength={200}
                placeholder="使用用途或创建新工作空间的原因"
                showCount={true}
              />
            </Form.Item>
            <Form.Item label="描述" name="remark">
              <Input.TextArea maxLength={100} placeholder="备注或空间说明" showCount={true} />
            </Form.Item>
            <Form.Item label={null}>
              <div>tips: 申请后由系统负责人进行审核处理</div>
            </Form.Item>
            <Form.Item label={null}>
              <Button htmlType="submit" type="primary">
                确认
              </Button>
            </Form.Item>
          </Form>
        </Spin>
      </Modal>
    </>
  );
}
