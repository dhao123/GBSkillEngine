# GBSkillEngine

MRO国标技能引擎平台 - 国标 -> Skills 技能 -> 知识图谱 -> 物料标准化梳理

## 项目简介

GBSkillEngine 是一个面向 MRO 工业品领域的智能化物料标准化平台，核心能力是将国家标准文档编译为可执行的 Skill DSL，并通过知识图谱和规则引擎技术实现非结构化物料描述的自动梳理和标准化。

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Alembic
- **数据库**: PostgreSQL 15+ / Neo4j 5.x
- **前端**: React 18 / TypeScript / Vite / Ant Design 5 / Monaco Editor
- **图谱可视化**: AntV G6
- **部署**: Docker / Docker Compose / Nginx

## 快速开始

### 方式一: Docker Compose 一键启动 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url>
cd GBSkillEngine

# 2. 复制环境变量配置
cp .env.example .env

# 3. 启动所有服务
./scripts/deploy.sh dev

# 或者直接使用 docker-compose
docker-compose up -d
```

**服务访问地址:**
- 前端界面: http://localhost:5173
- 后端API: http://localhost:8000
- API文档 (Swagger): http://localhost:8000/docs
- API文档 (ReDoc): http://localhost:8000/redoc
- Neo4j Browser: http://localhost:7474

### 方式二: 本地开发启动

#### 1. 环境准备

```bash
# 复制环境变量配置
cp .env.example .env

# 启动数据库服务 (PostgreSQL + Neo4j)
docker-compose up -d postgres neo4j
```

#### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 初始化示例数据 (可选)
python -m app.utils.init_sample_data

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 部署脚本使用

项目提供了便捷的部署脚本 `scripts/deploy.sh`:

```bash
# 显示帮助
./scripts/deploy.sh help

# 启动开发环境
./scripts/deploy.sh dev

# 启动生产环境
./scripts/deploy.sh prod

# 停止所有服务
./scripts/deploy.sh stop

# 重启服务
./scripts/deploy.sh restart

# 查看服务状态
./scripts/deploy.sh status

# 查看日志 (全部)
./scripts/deploy.sh logs

# 查看特定服务日志
./scripts/deploy.sh logs backend
./scripts/deploy.sh logs frontend

# 运行数据库迁移
./scripts/deploy.sh migrate

# 进入后端容器shell
./scripts/deploy.sh shell

# 清理所有容器和数据卷 (谨慎使用)
./scripts/deploy.sh clean
```

## 环境变量配置

主要配置项 (`.env` 文件):

```bash
# 环境模式
ENV=development  # development / production

# PostgreSQL
POSTGRES_USER=gbskill
POSTGRES_PASSWORD=gbskill123
POSTGRES_DB=gbskillengine

# Neo4j
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123

# 后端
BACKEND_PORT=8000
SECRET_KEY=your-secret-key-change-in-production
LOG_LEVEL=INFO

# 前端
FRONTEND_PORT=5173
VITE_API_BASE_URL=http://localhost:8000
```

## 核心功能

### 1. 国标管理
- 上传国标文档 (PDF/Word)
- 自动识别标准编号、名称、领域
- 在线预览和下载文档
- 编译为 Skill DSL (实时进度反馈)

### 2. Skill 管理
- Skill DSL 在线编辑 (Monaco Editor, 语法高亮)
- DSL 语法实时校验
- 版本历史管理和对比 (Diff View)
- Skill 测试功能
- 激活/停用控制

### 3. 物料梳理
- 输入非结构化物料描述
- 自动匹配合适的 Skill
- 输出结构化物料信息
- 批量处理和导出 (Excel/CSV)
- 置信度阈值配置
- 人工审核修正功能
- 梳理历史记录查看

### 4. 知识图谱
- 可视化展示国标知识图谱 (AntV G6)
- 多种布局切换 (力导向/层级/圆形/辐射)
- 节点详情面板
- 节点搜索高亮
- 关系类型过滤
- 节点类型图例交互

### 5. 可观测性
- 执行日志查询和导出
- 日期范围筛选
- 执行趋势统计图表
- 系统健康状态监控

### 6. 首页仪表盘
- 功能入口快捷卡片
- 系统健康状态展示
- 关键业务指标统计

## 项目结构

```
GBSkillEngine/
├── backend/                       # 后端服务
│   ├── app/
│   │   ├── api/v1/               # API路由
│   │   ├── models/               # 数据模型
│   │   ├── schemas/              # Pydantic Schemas
│   │   ├── services/             # 业务逻辑
│   │   │   ├── skill_compiler/   # Skill编译器
│   │   │   └── skill_runtime/    # Skill运行时引擎
│   │   ├── core/                 # 核心基础设施
│   │   │   ├── database.py       # 数据库连接
│   │   │   ├── neo4j_client.py   # Neo4j客户端
│   │   │   └── exceptions.py     # 统一异常处理
│   │   └── utils/                # 工具函数
│   ├── alembic/                  # 数据库迁移
│   ├── tests/                    # 单元测试
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                      # 前端应用
│   ├── src/
│   │   ├── components/           # 公共组件
│   │   │   ├── Layout.tsx        # 布局组件
│   │   │   └── ErrorBoundary.tsx # 错误边界
│   │   ├── contexts/             # React Context
│   │   │   └── LoadingContext.tsx
│   │   ├── pages/                # 页面组件
│   │   │   ├── Home/             # 首页
│   │   │   ├── Standards/        # 国标管理
│   │   │   ├── Skills/           # Skill管理
│   │   │   ├── MaterialParse/    # 物料梳理
│   │   │   ├── KnowledgeGraph/   # 知识图谱
│   │   │   └── Observability/    # 可观测性
│   │   ├── services/             # API调用
│   │   └── styles/               # 样式
│   ├── package.json
│   └── Dockerfile
│
├── nginx/                         # Nginx配置
│   └── nginx.conf
│
├── scripts/                       # 部署脚本
│   ├── deploy.sh                 # 部署管理脚本
│   └── init-db.sql               # 数据库初始化
│
├── docker-compose.yml            # 开发环境配置
├── docker-compose.prod.yml       # 生产环境配置
├── .env.example                  # 环境变量模板
└── README.md
```

## 示例物料梳理

输入: `UPVC管PN1.6-DN100`

输出:
```json
{
  "物料名称": "PVC-U管 DN100",
  "类目": "管材/塑料管/PVC-U管",
  "规格参数": {
    "公称直径DN": 100,
    "公称外径": 110,
    "公称压力PN": 1.6,
    "最小壁厚": 5.3,
    "材质": "PVC-U"
  },
  "适用标准": "GB/T 4219.1-2021",
  "置信度": 0.89
}
```

## API 文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要 API 模块

| 模块 | 路径前缀 | 说明 |
|------|----------|------|
| 国标管理 | `/api/v1/standards` | 国标上传、查询、编译 |
| Skills技能族 | `/api/v1/skills` | Skill CRUD、版本管理 |
| 物料梳理 | `/api/v1/material-parse` | 物料解析、批量处理 |
| 知识图谱 | `/api/v1/knowledge-graph` | 图谱数据查询 |
| 可观测性 | `/api/v1/observability` | 执行日志、统计 |

## 运行测试

```bash
cd backend

# 激活虚拟环境
source venv/bin/activate

# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=app

# 运行特定测试文件
pytest tests/test_standards_api.py -v
```

## 生产部署

```bash
# 1. 配置生产环境变量
cp .env.example .env
# 编辑 .env，设置生产环境密码和密钥

# 2. 启动生产环境
./scripts/deploy.sh prod

# 或使用 docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

生产环境将启动 Nginx 反向代理，提供:
- HTTP (80端口) / HTTPS (443端口，需配置SSL证书)
- 静态资源缓存
- Gzip压缩
- 安全头配置

## License

MIT
