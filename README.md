# POW_SE - 软件工程知识图谱平台

面向《软件工程》课程的多模态知识图谱增量式构建平台，采用Neo4j构建课程知识点知识图谱，支持图谱可视化、知识查询和智能问答。

## 贡献者

1. 俞烨
2. 张鸿榜
3. 张璟文
4. 王劲毅
5. 李嘉艺
6. 黄绍华
7. 张天硕
8. 刘方博
9. 陈欣

## 技术栈

### 前端技术栈
- **框架**: Vue 3 + TypeScript + Vite
- **UI组件库**: Naive UI
- **可视化**: Cytoscape.js + ECharts
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **国际化**: vue-i18n

### 后端技术栈
- **框架**: FastAPI + Python
- **图数据库**: Neo4j 5.x
- **缓存**: Redis
- **AI集成**: OpenAI API + 自定义GraphRAG算法
- **任务队列**: RQ (Redis Queue)

### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: Neo4j + Redis
- **部署**: 支持本地开发和容器化部署

## 项目结构
```lua
POW_SE/
├── app/vue/                    # Vue 3前端项目
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   │   ├── Dashboard.vue   # 仪表盘
│   │   │   ├── Upload.vue      # 文档上传
│   │   │   ├── Graph.vue       # 图谱可视化
│   │   │   ├── Query.vue       # 知识查询
│   │   │   └── Status.vue      # 处理状态
│   │   ├── components/         # 公共组件
│   │   ├── api/                # API服务
│   │   ├── stores/             # 状态管理
│   │   └── i18n/               # 国际化
│   ├── package.json
│   └── vite.config.ts
├── server/                     # FastAPI后端项目
│   ├── main.py                 # 应用入口文件
│   ├── routes/                 # API路由
│   │   ├── upload.py           # 文档上传
│   │   ├── ingest.py           # 知识抽取
│   │   ├── graph.py            # 图谱查询
│   │   └── knowledge_card.py   # 知识卡片
│   ├── services/               # 业务服务
│   │   ├── parser.py           # 文档解析
│   │   ├── extractor.py        # 知识抽取
│   │   ├── graph_service.py    # 图谱服务
│   │   └── linker.py           # 实体链接
│   ├── graphrag/               # GraphRAG模块
│   │   ├── stages/             # 8个构建阶段
│   │   ├── models/             # 数据模型
│   │   ├── config/             # 配置文件
│   │   └── utils/              # 工具函数
│   ├── infra/                  # 基础设施
│   │   ├── neo4j_client.py     # Neo4j客户端
│   │   └── ai_providers.py     # AI服务提供商
│   ├── models/                 # 数据模型
│   └── tests/                  # 测试代码
├── docker-compose.yml          # Docker Compose配置
├── uploads/                    # 上传文件目录
└── data/                       # 数据文件
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js 14+
- Neo4j 5.x
- Redis 6.x

### 安装依赖

**后端依赖:**
```bash
cd server
pip install -r requirements.txt
```

**前端依赖:**
```bash
cd app/vue
npm install
```

### 启动服务

**启动后端:**
```bash
cd server
python main.py
# 或使用PowerShell脚本
.\start-api.ps1
```

**启动前端:**
```bash
cd app/vue
npm run dev
# 或使用PowerShell脚本
.\start-frontend.ps1
```

### 访问应用

- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 功能特性

- 📊 **知识图谱可视化**: 使用Cytoscape.js实现交互式图谱展示
- 🔍 **智能搜索**: 支持关键词搜索和语义查询
- 📚 **多模态资源**: 关联文档、视频、代码等学习资源
- 🤖 **AI知识抽取**: 基于GraphRAG算法的知识实体识别
- 🔄 **增量构建**: 支持知识图谱的持续更新和扩展
- 🎯 **智能问答**: 基于知识图谱的智能问答系统

## 核心模块

### GraphRAG知识图谱构建
- **阶段0**: 篇章切分 - 智能文档分块
- **阶段1**: 指代消解 - 实体引用解析
- **阶段2**: 实体链接 - 概念识别与链接
- **阶段3**: 论断抽取 - 知识三元组提取
- **阶段4**: 主题社区 - 主题聚类与总结
- **阶段5**: 谓词治理 - 关系规范化
- **阶段6**: 幂等落库 - 数据持久化
- **阶段7**: GraphRAG检索 - 智能检索系统

### 知识卡片管理
- 概念节点管理
- 关系连接管理
- 证据回溯支持
- 增量更新机制

## 开发指南

### 后端开发

后端采用FastAPI框架，遵循RESTful API设计原则：

```python
# 示例API端点
@app.get("/api/graph/nodes")
async def get_graph_nodes(limit: int = 100):
    """获取图谱节点数据"""
    return neo4j_client.get_nodes(limit=limit)
```

### 前端开发

前端采用Vue 3组合式API，组件化开发：

```vue
<template>
  <GraphVisualization :graph-data="graphData" />
</template>

<script setup>
import { ref } from 'vue'
const graphData = ref(null)
</script>
```

## 部署说明

使用Docker Compose进行容器化部署：

```bash
docker-compose up -d
```

服务包括：
- **前端**: Vue应用 (端口8788)
- **后端**: FastAPI应用 (端口8000)
- **数据库**: Neo4j图数据库
- **缓存**: Redis缓存服务

## 测试

项目包含完整的测试框架：

```bash
# 运行单元测试
cd server
pytest tests/

# 运行GraphRAG模块测试
pytest tests/graphrag/
```

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 许可证

MIT License