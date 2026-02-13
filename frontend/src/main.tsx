import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import { LoadingProvider, GlobalLoading } from './contexts/LoadingContext'
import ErrorBoundary from './components/ErrorBoundary'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#676BEF',
            borderRadius: 6,
          },
        }}
      >
        <LoadingProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
          <GlobalLoading />
        </LoadingProvider>
      </ConfigProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
