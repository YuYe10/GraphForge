# 软件工程知识图谱平台

面向《软件工程》的多模态知识图谱增量式构建平台，采用Neo4j构建课程知识点知识图谱，支持图谱显示和知识点查询相关学习内容与数字化资源。

## 贡献者

1. 俞烨
2. 张鸿榜
3. 张璟文
4. 王劲毅
5. 李嘉艺

## 技术栈

- **前端**: Vue 3 + Vite + D3.js
- **后端**: FastAPI + Python
- **数据库**: Neo4j (图数据库) + MariaDB (关系数据库)
- **AI框架**: PyTorch + Transformers

## 项目结构
```lua
software_engineering_kg_platform/
├── backend/                    # FastAPI 后端项目
│   └── main.py                # 应用入口文件
├── frontend/                   # Vue.js 前端项目
├── kg_builder/                 # 知识图谱构建器模块（可独立运行）
├── database/                  # 数据库相关文件
├── docs/                      # 项目文档
└── docker-compose.yml         # Docker Compose 配置文件（用于 MariaDB 等服务）
```
## 快速开始

### 环境要求

- Python 3.8+
- Node.js 14+
- Neo4j 5.x
- MariaDB 10.x

### 安装依赖

**后端依赖:**
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖:**
```bash
cd frontend
npm install
```

### 启动服务

**启动后端:**
```bash
cd backend
python main.py
# 或使用批处理文件
start_backend.bat
```

**启动前端:**
```bash
cd frontend
npm run dev
# 或使用批处理文件
start_frontend.bat
```

### 访问应用

- 前端应用: http://localhost:8080
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 功能特性

- 📊 **知识图谱可视化**: 使用D3.js实现交互式图谱展示
- 🔍 **智能搜索**: 支持关键词搜索和语义查询
- 📚 **多模态资源**: 关联文档、视频、代码等学习资源
- 🤖 **AI知识抽取**: 基于BERT模型的知识实体识别
- 🔄 **增量构建**: 支持知识图谱的持续更新和扩展

## 开发指南

### 后端开发

后端采用FastAPI框架，遵循RESTful API设计原则：

```python
# 示例API端点
@app.get("/api/knowledge-graph/initial")
async def get_initial_graph():
    """获取初始知识图谱数据"""
    return neo4j_service.get_initial_graph()
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

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 许可证

MIT License