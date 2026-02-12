# GBSkillEngine

MRO国标技能引擎平台 - 国标 -> Skill 编译 -> 知识图谱 -> 物料标准化梳理

## 项目简介

GBSkillEngine 是一个面向 MRO 工业品领域的智能化物料标准化平台，核心能力是将国家标准文档编译为可执行的 Skill DSL，并通过知识图谱和规则引擎技术实现非结构化物料描述的自动梳理和标准化。

## 技术栈

- **后端**: Python 3.11+ / FastAPI / SQLAlchemy 2.0
- **数据库**: PostgreSQL 15+ / Neo4j 5.x
- **前端**: React 18 / TypeScript / Vite / Ant Design 5
- **图谱可视化**: AntV G6

## 快速开始

### 1. 环境准备

```bash
# 复制环境变量配置
cp .env.example .env

# 启动数据库服务 (PostgreSQL + Neo4j)
docker-compose up -d postgres neo4j
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化示例数据
python -m app.utils.init_sample_data

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看API文档

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173

### 4. Docker Compose 一键启动 (可选)

```bash
docker-compose up -d
```

## 核心功能

### 1. 国标管理
- 上传国标文档 (PDF/Word)
- 自动识别标准编号、名称、领域
- 编译为 Skill DSL

### 2. Skill 管理
- Skill DSL 在线编辑
- 版本管理
- 激活/停用控制

### 3. 物料梳理
- 输入非结构化物料描述
- 自动匹配合适的 Skill
- 输出结构化物料信息
- 展示执行 Trace

### 4. 知识图谱
- 可视化展示国标知识图谱
- 节点关系浏览

### 5. 执行日志
- 查看物料梳理执行记录
- 分析执行 Trace

## 项目结构

```
GBSkillEngine/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/            # API路由
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic Schemas
│   │   ├── services/          # 业务逻辑
│   │   │   ├── skill_compiler/    # Skill编译器
│   │   │   └── skill_runtime/     # Skill运行时引擎
│   │   ├── core/              # 核心基础设施
│   │   └── utils/             # 工具函数
│   └── requirements.txt
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── pages/             # 页面
│   │   ├── services/          # API调用
│   │   └── styles/            # 样式
│   └── package.json
│
├── docker-compose.yml
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

## License

MIT
