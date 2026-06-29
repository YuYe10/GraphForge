"""
Knowledge Card Models
=====================

知识卡片数据模型，用于用户手动创建和管理概念知识的 CRUD 操作。

Defines the request/response Pydantic models for knowledge card CRUD operations.
Knowledge cards represent user-curated concept entries in the knowledge graph
with rich metadata including aliases, relations, and custom attributes.

Classes / 类说明:
    KnowledgeCardCreate:   创建知识卡片请求 / Creation request
    KnowledgeCardUpdate:   更新知识卡片请求 / Update request
    KnowledgeCardResponse: 知识卡片响应 / Response model
    KnowledgeCardListResponse: 知识卡片列表响应 / List response model
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class KnowledgeCardCreate(BaseModel):
    """
    Knowledge card creation request model.
    知识卡片创建请求模型。

    Attributes:
        name:              Card name (concept name) / 卡片名称（概念名称）
        description:       Description of the concept / 概念描述
        domain:            Knowledge domain / 知识领域/分类
        category:          Concept category / 概念类别
        importance:        Importance level (low/medium/high) / 重要性级别
        tags:              Tag list for classification / 标签列表
        aliases:           Alternative names / 别名列表
        related_concepts:  Related concept names / 关联概念名称列表
        attributes:        Custom key-value properties / 自定义属性
    """
    name: str = Field(..., description="知识卡片名称")
    description: Optional[str] = Field(None, description="描述")
    domain: Optional[str] = Field(None, description="领域/分类")
    category: Optional[str] = Field(None, description="类别")
    importance: Optional[str] = Field(
        "medium",
        description="重要性: low/medium/high"
    )
    tags: List[str] = Field(default_factory=list, description="标签列表")
    aliases: List[str] = Field(default_factory=list, description="别名列表")
    related_concepts: List[str] = Field(
        default_factory=list,
        description="关联概念名称列表"
    )
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="自定义属性"
    )


class KnowledgeCardUpdate(BaseModel):
    """
    Knowledge card update request model.
    知识卡片更新请求模型。

    All fields are optional — only provided fields will be updated.
    所有字段都是可选的 — 仅更新提供的字段。

    Attributes:
        name:              New card name / 新卡片名称
        description:       New description / 新描述
        domain:            New domain / 新领域
        category:          New category / 新类别
        importance:        New importance level / 新重要性级别
        tags:              New tag list (replaces existing) / 新标签列表
        aliases:           New alias list (replaces existing) / 新别名列表
        related_concepts:  New related concepts (replaces existing) / 新关联概念
        attributes:        New custom attributes (merged) / 新自定义属性
    """
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[str] = None
    tags: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    related_concepts: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None


class KnowledgeCardResponse(BaseModel):
    """
    Knowledge card response model.
    知识卡片响应模型。

    Contains full card data including computed fields like connection_count.
    包含完整的卡片数据，包括 connection_count 等计算字段。

    Attributes:
        id:               Card identifier (concept name) / 卡片标识（概念名称）
        name:             Concept name / 概念名称
        description:      Description / 描述
        domain:           Knowledge domain / 知识领域
        category:         Concept category / 概念类别
        importance:       Importance level / 重要性级别
        tags:             Tag list / 标签列表
        aliases:          Alias list / 别名列表
        related_concepts: Related concept names / 关联概念名称列表
        attributes:       Custom attributes / 自定义属性
        created_at:       Creation timestamp / 创建时间
        updated_at:       Last update timestamp / 最后更新时间
        connection_count: Number of graph connections / 图连接数
    """
    id: str
    name: str
    description: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    importance: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    connection_count: int = 0

    model_config = {"from_attributes": True}


class KnowledgeCardListResponse(BaseModel):
    """
    Knowledge card list response model.
    知识卡片列表响应模型。

    Attributes:
        cards: List of knowledge cards / 知识卡片列表
        total: Total count (for pagination) / 总数量（用于分页）
    """
    cards: List[KnowledgeCardResponse]
    total: int
