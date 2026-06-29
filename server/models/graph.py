"""
Graph Data Models
=================

知识图谱相关的数据模型，定义节点、边、查询和响应结构。

Defines the Pydantic models for knowledge graph operations, including
node, edge, query, and response structures used by the graph API.

Classes / 类说明:
    Node:             Graph node with labels and properties / 图谱节点
    Edge:             Graph edge with source, target, type, and properties / 图谱边
    GraphQuery:       Graph query request (Cypher string) / 图谱查询请求
    GraphResponse:    Graph query response (nodes + edges) / 图谱查询响应
    NodeCreate:       Node creation request / 节点创建请求
    NodeUpdate:       Node update request / 节点更新请求
    EdgeCreate:       Edge creation request / 边创建请求
    EdgeUpdate:       Edge update request / 边更新请求
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Node(BaseModel):
    """
    Graph node model.
    图谱节点模型。

    Represents a node in the knowledge graph with its labels and properties.
    表示知识图谱中的一个节点，包含标签和属性。

    Attributes:
        id:          Unique node identifier / 唯一节点标识
        labels:      Node labels (e.g., ["Concept", "Person"]) / 节点标签
        properties:  Node properties dictionary / 节点属性字典
    """
    id: str
    labels: List[str]
    properties: Dict[str, Any]


class Edge(BaseModel):
    """
    Graph edge (relationship) model.
    图谱边（关系）模型。

    Represents a directed relationship between two nodes in the knowledge graph.
    表示知识图谱中两个节点之间的有向关系。

    Attributes:
        id:          Optional edge identifier / 可选的边标识
        source:      Source node ID / 源节点ID
        target:      Target node ID / 目标节点ID
        type:        Relationship type (e.g., "MENTIONS", "IS_A") / 关系类型
        properties:  Relationship properties / 关系属性
    """
    id: Optional[str] = None
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphQuery(BaseModel):
    """
    Graph query request model.
    图谱查询请求模型。

    Wraps a Cypher query string for direct database access.
    封装用于直接数据库访问的 Cypher 查询字符串。

    Attributes:
        cypher:  Cypher query string / Cypher 查询语句
        limit:   Maximum number of results / 最大结果数
    """
    cypher: Optional[str] = None
    limit: int = 100


class GraphResponse(BaseModel):
    """
    Graph query response model.
    图谱查询响应模型。

    Contains the nodes and edges returned from a graph query.
    包含从图谱查询返回的节点和边。

    Attributes:
        nodes:  List of nodes / 节点列表
        edges:  List of edges / 边列表
        stats:  Optional query statistics / 可选的查询统计信息
    """
    nodes: List[Node]
    edges: List[Edge]
    stats: Optional[Dict[str, Any]] = None


class NodeCreate(BaseModel):
    """
    Node creation request model.
    节点创建请求模型。

    Attributes:
        labels:     Node labels (at least one required) / 节点标签（至少需要一个）
        properties: Node properties / 节点属性
    """
    labels: List[str] = Field(..., description="Node labels", min_length=1)
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Node properties"
    )


class NodeUpdate(BaseModel):
    """
    Node update request model.
    节点更新请求模型。

    Attributes:
        labels:            New labels (replaces existing) / 新标签（替换现有）
        properties:        Properties to merge / 要合并的属性
        remove_properties: Properties to remove / 要删除的属性
    """
    labels: Optional[List[str]] = Field(
        None,
        description="New labels (replaces existing)"
    )
    properties: Dict[str, Any] = Field(
        ...,
        description="Properties to update (merge with existing)"
    )
    remove_properties: Optional[List[str]] = Field(
        None,
        description="Properties to remove"
    )


class EdgeCreate(BaseModel):
    """
    Edge creation request model.
    边创建请求模型。

    Attributes:
        source:     Source node ID / 源节点ID
        target:     Target node ID / 目标节点ID
        type:       Relationship type / 关系类型
        properties: Relationship properties / 关系属性
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relationship properties"
    )


class EdgeUpdate(BaseModel):
    """
    Edge update request model.
    边更新请求模型。

    Attributes:
        type:              New relationship type / 新关系类型
        properties:        Properties to merge / 要合并的属性
        remove_properties: Properties to remove / 要删除的属性
    """
    type: Optional[str] = Field(None, description="New relationship type")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Properties to update"
    )
    remove_properties: Optional[List[str]] = Field(
        None,
        description="Properties to remove"
    )
