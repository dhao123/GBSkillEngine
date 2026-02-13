/**
 * 错误边界组件 - 捕获React组件树中的JavaScript错误
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card } from 'antd';
import { ReloadOutlined, HomeOutlined, BugOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    
    // 调用错误回调
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // 记录错误到控制台
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // 如果提供了自定义fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // 默认错误UI
      return (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '100vh',
          padding: 24,
          backgroundColor: '#f5f5f5'
        }}>
          <Result
            status="error"
            title="页面出现异常"
            subTitle="抱歉，页面发生了错误。请尝试刷新页面或返回首页。"
            extra={[
              <Button 
                key="retry" 
                onClick={this.handleRetry}
                icon={<ReloadOutlined />}
              >
                重试
              </Button>,
              <Button 
                key="reload" 
                type="primary" 
                onClick={this.handleReload}
                icon={<ReloadOutlined />}
              >
                刷新页面
              </Button>,
              <Button 
                key="home" 
                onClick={this.handleGoHome}
                icon={<HomeOutlined />}
              >
                返回首页
              </Button>,
            ]}
          >
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Card 
                title={
                  <span>
                    <BugOutlined style={{ marginRight: 8 }} />
                    错误详情 (仅开发环境显示)
                  </span>
                }
                size="small"
                style={{ 
                  marginTop: 24, 
                  textAlign: 'left',
                  maxWidth: 800,
                  margin: '24px auto 0'
                }}
              >
                <Paragraph>
                  <Text strong>错误信息: </Text>
                  <Text type="danger">{this.state.error.message}</Text>
                </Paragraph>
                {this.state.error.stack && (
                  <Paragraph>
                    <Text strong>堆栈跟踪:</Text>
                    <pre style={{ 
                      fontSize: 12, 
                      background: '#f5f5f5', 
                      padding: 12, 
                      borderRadius: 4,
                      overflow: 'auto',
                      maxHeight: 200
                    }}>
                      {this.state.error.stack}
                    </pre>
                  </Paragraph>
                )}
                {this.state.errorInfo?.componentStack && (
                  <Paragraph>
                    <Text strong>组件堆栈:</Text>
                    <pre style={{ 
                      fontSize: 12, 
                      background: '#f5f5f5', 
                      padding: 12, 
                      borderRadius: 4,
                      overflow: 'auto',
                      maxHeight: 200
                    }}>
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </Paragraph>
                )}
              </Card>
            )}
          </Result>
        </div>
      );
    }

    return this.props.children;
  }
}

// 页面级错误边界 - 更紧凑的错误展示
export const PageErrorBoundary: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={
        <Result
          status="warning"
          title="页面加载失败"
          subTitle="当前页面出现问题，请稍后重试"
          extra={
            <Button type="primary" onClick={() => window.location.reload()}>
              刷新页面
            </Button>
          }
        />
      }
    >
      {children}
    </ErrorBoundary>
  );
};

// 组件级错误边界 - 更小的错误展示
interface ComponentErrorBoundaryProps {
  children: ReactNode;
  componentName?: string;
}

export const ComponentErrorBoundary: React.FC<ComponentErrorBoundaryProps> = ({ 
  children, 
  componentName 
}) => {
  return (
    <ErrorBoundary
      fallback={
        <Card size="small" style={{ textAlign: 'center', color: '#999' }}>
          <BugOutlined style={{ fontSize: 24, marginBottom: 8 }} />
          <div>{componentName ? `${componentName}加载失败` : '组件加载失败'}</div>
          <Button 
            size="small" 
            type="link" 
            onClick={() => window.location.reload()}
          >
            刷新页面
          </Button>
        </Card>
      }
    >
      {children}
    </ErrorBoundary>
  );
};

export default ErrorBoundary;
