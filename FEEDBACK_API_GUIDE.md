# 反馈 API 使用指南

## 概述
完整的用户反馈和知识图谱修正工作流系统。支持实体合并、数据修正、关系解链、请求列表和审核批准。

## 已实现的端点

### 1. 提交合并请求
**POST** `/feedback/merge`

合并两个相似或重复的实体。

**请求体**:
```json
{
  "source_concept_id": "BERT",
  "target_concept_id": "Bidirectional Encoder Representations from Transformers",
  "reason": "这两个是同一个概念"
}
```

**响应**:
```json
{
  "id": "merge_9a2f1c8d",
  "source_concept_id": "BERT",
  "target_concept_id": "Bidirectional Encoder Representations from Transformers",
  "reason": "这两个是同一个概念",
  "status": "pending",
  "created_at": "2025-12-05T06:20:48.273768",
  "reviewed_at": null,
  "review_comment": null
}
```

### 2. 提交修正请求
**POST** `/feedback/correction`

提交数据修正或更新请求。

**请求体**:
```json
{
  "object_type": "Entity",
  "object_id": "BERT",
  "field": "definition",
  "old_value": "旧的定义",
  "new_value": "新的更正定义",
  "reason": "原定义不准确"
}
```

**响应**:
```json
{
  "id": "corr_7b3e2d9c",
  "object_type": "Entity",
  "object_id": "BERT",
  "field": "definition",
  "old_value": "旧的定义",
  "new_value": "新的更正定义",
  "reason": "原定义不准确",
  "status": "pending",
  "created_at": "2025-12-05T06:20:48.273768",
  "reviewed_at": null,
  "review_comment": null
}
```

### 3. 提交解链请求
**POST** `/feedback/unlink`

从文档中取消一个概念的链接（表示该链接不正确）。

**请求体**:
```json
{
  "mention_text": "深度学习",
  "chunk_id": "chunk_123",
  "linked_concept_id": "深度学习",
  "reason": "这个提及应该链接到其他概念"
}
```

**响应**:
```json
{
  "id": "unlink_8c4f3a1b",
  "mention_text": "深度学习",
  "chunk_id": "chunk_123",
  "linked_concept_id": "深度学习",
  "reason": "这个提及应该链接到其他概念",
  "status": "pending",
  "created_at": "2025-12-05T06:20:48.273768",
  "reviewed_at": null,
  "review_comment": null
}
```

### 4. 查询待审核请求
**GET** `/feedback/pending`

列出所有待审核的反馈请求。

**查询参数**:
- `limit` (可选，默认 20): 返回的最大记录数

**响应**:
```json
{
  "merge_requests": [
    {
      "id": "merge_9a2f1c8d",
      "source_concept_id": "BERT",
      "target_concept_id": "Bidirectional Encoder Representations from Transformers",
      "reason": "这两个是同一个概念",
      "status": "pending",
      "created_at": "2025-12-05T06:20:48.273768"
    }
  ],
  "correction_requests": [
    {
      "id": "corr_7b3e2d9c",
      "object_type": "Entity",
      "object_id": "BERT",
      "field": "definition",
      "old_value": "旧的定义",
      "new_value": "新的更正定义",
      "reason": "原定义不准确",
      "status": "pending",
      "created_at": "2025-12-05T06:20:48.273768"
    }
  ],
  "unlink_requests": [
    {
      "id": "unlink_8c4f3a1b",
      "mention_text": "深度学习",
      "chunk_id": "chunk_123",
      "linked_concept_id": "深度学习",
      "reason": "这个提及应该链接到其他概念",
      "status": "pending",
      "created_at": "2025-12-05T06:20:48.273768"
    }
  ],
  "total": 3
}
```

### 5. 审核和批准请求
**POST** `/feedback/review/{request_id}`

审核用户的反馈请求并批准或拒绝。

**路径参数**:
- `request_id`: 要审核的请求 ID

**请求体**:
```json
{
  "action": "approve",
  "comment": "已验证，同意合并"
}
```

**响应**:
```json
{
  "id": "merge_9a2f1c8d",
  "source_concept_id": "BERT",
  "target_concept_id": "Bidirectional Encoder Representations from Transformers",
  "reason": "这两个是同一个概念",
  "status": "approved",
  "created_at": "2025-12-05T06:20:48.273768",
  "reviewed_at": "2025-12-05T06:20:49.123456",
  "review_comment": "已验证，同意合并"
}
```

## 工作流示例

### 完整的合并请求工作流

```bash
# 1. 用户提交合并请求
curl -X POST http://localhost:8000/feedback/merge \
  -H "Content-Type: application/json" \
  -d '{
    "source_concept_id": "BERT",
    "target_concept_id": "Bidirectional Encoder Representations from Transformers",
    "reason": "这两个是同一个概念"
  }'
# 返回: merge_9a2f1c8d (status: pending)

# 2. 查询所有待审核请求
curl http://localhost:8000/feedback/pending

# 3. 审核管理员审查并批准
curl -X POST http://localhost:8000/feedback/review/merge_9a2f1c8d \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "comment": "已验证，同意合并"
  }'
# 返回: 更新的请求 (status: approved, reviewed_at: timestamp)

# 4. 或者拒绝请求
curl -X POST http://localhost:8000/feedback/review/merge_9a2f1c8d \
  -H "Content-Type: application/json" \
  -d '{
    "action": "reject",
    "comment": "这两个其实是不同的概念"
  }'
# 返回: 更新的请求 (status: rejected, reviewed_at: timestamp)
```

## 数据模型

### 请求状态
- `pending`: 已提交，等待审核
- `approved`: 已批准
- `rejected`: 已拒绝

### 时间戳格式
所有时间戳都使用 ISO 8601 格式的字符串：
- 格式: `YYYY-MM-DDTHH:MM:SS.ffffff`
- 示例: `2025-12-05T06:20:48.273768`
- 时区: UTC

### 请求 ID 格式
自动生成，格式为 `{type}_{random_suffix}`：
- 合并请求: `merge_9a2f1c8d`
- 修正请求: `corr_7b3e2d9c`
- 解链请求: `unlink_8c4f3a1b`

## Neo4j 存储结构

所有反馈请求都存储为 Neo4j 节点：

```cypher
// 合并请求节点
(merge:FeedbackRequest:MergeRequest {
  id: "merge_9a2f1c8d",
  source_concept_id: "BERT",
  target_concept_id: "Bidirectional Encoder...",
  reason: "这两个是同一个概念",
  status: "pending",
  created_at: "2025-12-05T06:20:48.273768",
  reviewed_at: null,
  review_comment: null
})

// 修正请求节点
(correction:FeedbackRequest:CorrectionRequest {
  id: "corr_7b3e2d9c",
  object_type: "Entity",
  object_id: "BERT",
  field: "definition",
  old_value: "旧定义",
  new_value: "新定义",
  reason: "原定义不准确",
  status: "pending",
  created_at: "2025-12-05T06:20:48.273768",
  reviewed_at: null,
  review_comment: null
})

// 解链请求节点
(unlink:FeedbackRequest:UnlinkRequest {
  id: "unlink_8c4f3a1b",
  mention_text: "深度学习",
  chunk_id: "chunk_123",
  linked_concept_id: "深度学习",
  reason: "应该链接到其他概念",
  status: "pending",
  created_at: "2025-12-05T06:20:48.273768",
  reviewed_at: null,
  review_comment: null
})
```

## 错误处理

### 常见错误

**400 Bad Request**
```json
{
  "detail": "请求体验证失败"
}
```

**404 Not Found**
```json
{
  "detail": "请求不存在"
}
```

**409 Conflict**
```json
{
  "detail": "概念不存在或请求状态无效"
}
```

## 集成建议

1. **前端表单**: 为每种反馈类型创建表单
2. **通知系统**: 当有新的待审核请求时通知管理员
3. **仪表板**: 显示待审核、已批准、已拒绝的统计
4. **审计日志**: 跟踪所有审核决定和时间戳
5. **自动化**: 根据批准的请求自动更新知识图谱

## 已完成的实现

✅ 所有 5 个 TODO 项已实现：
- `submit_merge_request()` - 提交合并请求
- `submit_correction_request()` - 提交修正请求
- `submit_unlink_request()` - 提交解链请求
- `list_pending_requests()` - 查询待审核请求
- `review_feedback()` - 审核和批准请求

✅ 所有端点已测试并正常工作
✅ 时间戳正确记录为 ISO 8601 字符串
✅ 所有数据已持久化到 Neo4j
