# 知识图谱可视化 & GraphRAG 主题查询 API 指南

## 概述

已完成知识图谱可视化的前后端集成以及 GraphRAG 主题查询 API，使得 Neo4j 数据库中的知识图谱和主题社区能成功显示在前端。

## 实现内容

### 后端 (Python/FastAPI)

#### 1. 新增可视化 API 端点

**文件**: `/home/yuye/POW/server/routes/graph.py`

**新增端点**: `GET /graph/visualize`

**功能**:
- 从 Neo4j 数据库查询节点和关系
- 自动处理 Neo4j 特殊类型转换（DateTime、Node 对象等）
- 返回前端可直接使用的可视化数据格式

**参数**:
- `limit` (int): 返回的最大节点数，默认 500，最大 5000
- `node_type` (str, 可选): 按节点类型过滤（如 Concept、Document 等）

**响应格式**:
```json
{
  "nodes": [
    {
      "id": "node_id",
      "labels": ["Concept"],
      "type": "Concept",
      "label": "显示标签",
      "degree": 3,
      "properties": { ... }
    }
  ],
  "edges": [
    {
      "id": "edge_id",
      "source": "source_id",
      "target": "target_id",
      "type": "RELATES_TO",
      "label": "RELATES_TO",
      "properties": { ... }
    }
  ],
  "stats": {
    "node_count": 100,
    "edge_count": 150,
    "types": ["Concept", "Document", ...]
  }
}
```

#### 2. Neo4j 类型转换优化

**文件**: `/home/yuye/POW/server/infra/neo4j_client.py`

**改进**:
- 自动将 Neo4j Node 对象转换为字典
- 自动将 Neo4j DateTime 转换为 Python datetime
- 递归处理嵌套的复杂类型

### 前端 (Vue 3 + TypeScript)

#### 1. API 服务更新

**文件**: `/home/yuye/POW/app/vue/src/api/services.ts`

**新增函数**:
```typescript
// 获取知识图谱数据
export const getGraphData = (limit: number = 500): Promise<any>

// 按类型获取知识图谱数据
export const getGraphDataByType = (nodeType: string, limit: number = 500): Promise<any>
```

#### 2. 前端组件更新

**文件**: `/home/yuye/POW/app/vue/src/views/Graph.vue`

**改进**:
- 更新 `loadGraph()` 函数以支持新的数据格式
- 正确处理节点标签、类型、度数等属性
- 改进 Cytoscape 数据映射

## 使用方法

### 1. 启动后端服务

```bash
cd /home/yuye/POW/server
python -m uvicorn main:app --reload --port 8000
```

### 2. 启动前端服务

```bash
cd /home/yuye/POW/app/vue
npm run dev
```

### 3. 访问知识图谱页面

打开浏览器访问: `http://localhost:5173`，然后导航到"知识图谱"页面

### 4. 加载知识图谱

点击"加载图谱"按钮，系统将自动从 Neo4j 数据库加载数据并展示

## 测试方式

### 方式 1: 命令行测试后端 API

```bash
cd /home/yuye/POW
python test_graph_visualization.py
```

### 方式 2: 使用 curl 测试

```bash
# 获取所有节点（限制 100）
curl "http://localhost:8000/graph/visualize?limit=100"

# 获取 Concept 类型的节点
curl "http://localhost:8000/graph/visualize?limit=50&node_type=Concept"

# 获取 Document 类型的节点
curl "http://localhost:8000/graph/visualize?limit=50&node_type=Document"
```

### 方式 3: 使用浏览器开发工具

1. 打开浏览器开发工具（F12）
2. 切换到 Network 标签
3. 点击"加载图谱"按钮
4. 查看 `/graph/visualize` 请求的响应数据

## 数据流程

```
Neo4j 数据库
    ↓
GraphService (数据查询与转换)
    ↓
/graph/visualize 端点
    ↓
前端 API 服务 (getGraphData)
    ↓
Graph.vue 组件 (loadGraph)
    ↓
Cytoscape 库 (渲染可视化)
    ↓
用户界面
```

## 功能特性

✅ **自动类型转换**: Neo4j 特殊类型自动转换为 Python/JSON 兼容格式

✅ **性能优化**: 支持限制返回节点数量，避免前端过载

✅ **灵活过滤**: 支持按节点类型过滤

✅ **完整信息**: 返回节点度数、标签、属性等完整信息

✅ **错误处理**: 完善的异常处理和错误日志

✅ **布局支持**: 前端支持多种布局方式（层级、圆形、力导向等）

## 常见问题

### Q1: 图谱加载失败，显示"no_data"

**解决方案**:
1. 检查 Neo4j 是否运行正常
2. 检查数据库中是否有数据
3. 查看浏览器控制台错误信息
4. 运行 `python test_graph_visualization.py` 测试后端 API

### Q2: 节点显示不完整或格式不对

**解决方案**:
1. 检查节点是否有 `name` 或 `id` 字段
2. 在浏览器 DevTools Network 标签中查看 API 响应格式
3. 确认前端 `loadGraph()` 函数正确处理了数据

### Q3: 边（关系）没有显示

**解决方案**:
1. 检查 Neo4j 中是否存在关系数据
2. 确认 Neo4j 查询正确返回了关系数据
3. 检查前端 Cytoscape 配置中的边样式是否正确

## 后续改进建议

1. **性能优化**:
   - 实现数据分页加载
   - 添加数据缓存机制
   - 使用虚拟滚动处理大图谱

2. **功能扩展**:
   - 添加图谱搜索和过滤
   - 实现节点聚合（合并相似节点）
   - 添加路径查询功能

3. **可视化增强**:
   - 自定义节点样式（颜色、图标等）
   - 添加热力图显示
   - 实现节点详情弹窗

4. **交互改进**:
   - 添加鼠标悬停提示
   - 实现拖拽创建关系
   - 添加撤销/重做功能

## 文件变更清单

| 文件 | 变更类型 | 说明 |
|-----|--------|------|
| `/server/routes/graph.py` | 新增 | 添加 `/graph/visualize` 端点 |
| `/server/infra/neo4j_client.py` | 改进 | 增强 Neo4j 类型转换 |
| `/app/vue/src/api/services.ts` | 更新 | 添加 `getGraphData` 函数 |
| `/app/vue/src/views/Graph.vue` | 更新 | 改进 `loadGraph()` 函数 |
| `/test_graph_visualization.py` | 新增 | 测试脚本 |

## 技术栈

**后端**:
- FastAPI
- Neo4j Python Driver
- Pydantic

**前端**:
- Vue 3
- TypeScript
- Cytoscape.js
- Naive UI

**数据库**:
- Neo4j 图数据库

---

## GraphRAG 主题查询 API (新增)

### 已实现的端点

#### 1. 列出所有主题
**GET** `/graphrag/themes`

查询所有主题社区，支持按文档 ID 过滤。

**查询参数**:
- `doc_id` (可选): 文档 ID，用于过滤特定文档的主题

**示例请求**:
```bash
curl http://localhost:8000/graphrag/themes
curl http://localhost:8000/graphrag/themes?doc_id=doc_123
```

**响应格式**:
```json
{
  "themes": [
    {
      "id": "theme_test_001",
      "label": "深度学习基础",
      "summary": "本主题涵盖深度学习的基础概念...",
      "level": 1,
      "keywords": ["深度学习", "神经网络", "反向传播"],
      "member_count": 15,
      "created_at": "2025-12-05T07:37:41.994000000+00:00"
    }
  ],
  "total": 1
}
```

#### 2. 获取主题详情
**GET** `/graphrag/theme/{theme_id}`

获取指定主题的详细信息，包括关联的概念和论断。

**路径参数**:
- `theme_id`: 主题 ID

**示例请求**:
```bash
curl http://localhost:8000/graphrag/theme/theme_test_001
```

**响应格式**:
```json
{
  "id": "theme_test_001",
  "label": "深度学习基础",
  "summary": "本主题涵盖深度学习的基础概念...",
  "level": 1,
  "keywords": ["深度学习", "神经网络", "反向传播"],
  "community_id": "comm_001",
  "member_count": 15,
  "concept_ids": ["神经网络", "反向传播", "梯度下降"],
  "claim_ids": ["claim_001", "claim_002"],
  "concepts": [
    {
      "name": "神经网络",
      "definition": "一种受生物神经系统启发的计算模型"
    }
  ],
  "claims": [
    {
      "id": "claim_001",
      "text": "深度学习模型需要大量数据进行训练"
    }
  ],
  "created_at": "2025-12-05T07:37:41.994000000+00:00",
  "updated_at": "2025-12-05T07:37:41.994000000+00:00"
}
```

### 主题层级说明

- **Level 1**: 粗粒度主题（覆盖广泛领域，成员多）
- **Level 2**: 细粒度主题（聚焦特定技术，成员少）

### 使用场景

1. **知识图谱可视化**: 获取主题用于可视化展示
2. **主题浏览器**: 构建主题导航和详情页面
3. **按文档过滤**: 查看特定文档的主题分布
4. **概念关联**: 通过主题发现概念之间的关系

### 测试数据

系统包含 3 个测试主题：
- 深度学习基础 (Level 1, 15 成员)
- Transformer 架构 (Level 2, 12 成员)
- 计算机视觉 (Level 1, 18 成员)

---

**最后更新**: 2025年12月5日
**版本**: 1.1
