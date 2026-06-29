"""
Knowledge Card API Routes
==========================

知识卡片 API 路由，提供用户手动管理概念的 CRUD 接口。

Provides RESTful CRUD endpoints for knowledge cards, which represent
user-curated concept entries in the knowledge graph. Knowledge cards
extend basic concepts with rich metadata including descriptions, aliases,
domains, categories, tags, and related concept links.

Endpoints / 接口列表::

    POST   /knowledge-cards           Create a card / 创建知识卡片
    GET    /knowledge-cards           List cards / 获取知识卡片列表
    GET    /knowledge-cards/{id}      Get a card / 获取单个知识卡片
    PUT    /knowledge-cards/{id}      Update a card / 更新知识卡片
    DELETE /knowledge-cards/{id}      Delete a card / 删除知识卡片

Data model / 数据模型::
    Concepts are stored as Neo4j :Concept nodes with properties.
    - Aliases are stored as :Alias nodes linked via :ALIAS_OF
    - Related concepts are linked via :RELATED edges
    - Connection count is computed dynamically via OPTIONAL MATCH
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from infra.neo4j_client import neo4j_client
from models.knowledge_card import (
    KnowledgeCardCreate,
    KnowledgeCardUpdate,
    KnowledgeCardResponse,
    KnowledgeCardListResponse,
)
from datetime import datetime

router = APIRouter(
    prefix="/knowledge-cards",
    tags=["knowledge-cards"],
)


def _format_timestamp(ts) -> Optional[str]:
    """
    Convert a timestamp value to ISO format string.
    将时间戳值转换为 ISO 格式字符串。

    Handles various input types: str, datetime, or None.

    Args:
        ts:  Timestamp value (str, datetime, or None)

    Returns:
        ISO 8601 formatted string, or None if input was None
    """
    if ts is None:
        return None
    if isinstance(ts, str):
        return ts
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)


@router.post("", response_model=KnowledgeCardResponse)
async def create_knowledge_card(card: KnowledgeCardCreate):
    """
    Create a new knowledge card (concept) in the knowledge graph.
    在知识图谱中创建一个新的知识卡片（概念）。

    POST /knowledge-cards

    Creates a Concept node with rich metadata, then creates Alias nodes
    and RELATED_TO relationships as specified. The response includes
    the full card data with computed connection count.

    Args:
        card:  Knowledge card creation data / 知识卡片创建数据

    Returns:
        KnowledgeCardResponse with all card fields / 完整的知识卡片响应

    Raises:
        400: If concept with same name already exists / 同名概念已存在
        500: If creation succeeds but query fails / 创建成功但查询失败
    """
    try:
        # Check for duplicate concept name / 检查是否已存在同名概念
        existing = neo4j_client.execute_query(
            "MATCH (c:Concept {name: $name}) RETURN c",
            {"name": card.name},
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"概念 '{card.name}' 已存在",
            )

        # Create concept node with properties / 创建概念节点
        now = datetime.utcnow().isoformat()
        properties = {
            "name": card.name,
            "description": card.description or "",
            "domain": card.domain or "",
            "category": card.category or "",
            "importance": card.importance or "medium",
            "tags": card.tags,
            "created_at": now,
            "updated_at": now,
            "source": "user_created",  # Mark as user-created / 标记为用户创建
        }

        # Merge custom attributes / 合并自定义属性
        if card.attributes:
            properties.update(card.attributes)

        neo4j_client.execute_query(
            """
            CREATE (c:Concept)
            SET c = $properties
            RETURN c
            """,
            {"properties": properties},
        )

        # Process aliases / 处理别名
        for alias in card.aliases:
            neo4j_client.execute_query(
                """
                MATCH (c:Concept {name: $name})
                MERGE (a:Alias {name: $alias})
                MERGE (a)-[:REFERS_TO]->(c)
                """,
                {"name": card.name, "alias": alias},
            )

        # Process related concepts / 处理关联概念
        for related_name in card.related_concepts:
            neo4j_client.execute_query(
                """
                MERGE (c1:Concept {name: $name1})
                MERGE (c2:Concept {name: $name2})
                MERGE (c1)-[:RELATED_TO]->(c2)
                """,
                {"name1": card.name, "name2": related_name},
            )

        # Query and return the created card / 查询并返回创建的卡片
        result = neo4j_client.execute_query(
            """
            MATCH (c:Concept {name: $name})
            OPTIONAL MATCH (c)-[r]-()
            WITH c, count(r) as conn_count
            OPTIONAL MATCH (a:Alias)-[:REFERS_TO]->(c)
            WITH c, conn_count, collect(a.name) as aliases
            RETURN c, conn_count, aliases
            """,
            {"name": card.name},
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="创建成功但无法查询到结果",
            )

        record = result[0]
        concept = record["c"]

        return KnowledgeCardResponse(
            id=concept.get("name"),
            name=concept.get("name"),
            description=concept.get("description"),
            domain=concept.get("domain"),
            category=concept.get("category"),
            importance=concept.get("importance"),
            tags=concept.get("tags", []),
            aliases=record.get("aliases", []),
            related_concepts=card.related_concepts,
            attributes=card.attributes,
            created_at=_format_timestamp(concept.get("created_at")),
            updated_at=_format_timestamp(concept.get("updated_at")),
            connection_count=record.get("conn_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"创建知识卡片失败: {str(e)}",
        )


@router.get("", response_model=KnowledgeCardListResponse)
async def list_knowledge_cards(
    domain: Optional[str] = Query(
        None, description="Filter by domain / 按领域筛选"
    ),
    category: Optional[str] = Query(
        None, description="Filter by category / 按类别筛选"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Max results / 返回数量限制"
    ),
    offset: int = Query(
        0, ge=0, description="Offset for pagination / 偏移量"
    ),
):
    """
    List knowledge cards with optional filtering and pagination.
    获取知识卡片列表，支持可选筛选和分页。

    GET /knowledge-cards

    Args:
        domain:    Filter by knowledge domain / 按领域筛选
        category:  Filter by category / 按类别筛选
        limit:     Maximum number of cards to return / 最大返回数量
        offset:    Pagination offset / 分页偏移量

    Returns:
        KnowledgeCardListResponse with cards list and total count
        包含卡片列表和总数的响应
    """
    try:
        # Build WHERE clause / 构建查询条件
        where_clauses = []
        params = {"limit": limit, "offset": offset}

        if domain:
            where_clauses.append("c.domain = $domain")
            params["domain"] = domain

        if category:
            where_clauses.append("c.category = $category")
            params["category"] = category

        where_clause = (
            "WHERE " + " AND ".join(where_clauses)
            if where_clauses
            else ""
        )

        # Query cards / 查询卡片
        query = f"""
        MATCH (c:Concept)
        {where_clause}
        OPTIONAL MATCH (c)-[r]-()
        WITH c, count(r) as conn_count
        OPTIONAL MATCH (a:Alias)-[r_alias]->(c)
        WITH c, conn_count, collect(a.name) as aliases
        OPTIONAL MATCH (c)-[r_rel]->(related:Concept)
        WITH c, conn_count, aliases, collect(related.name)
            as related_concepts
        RETURN c, conn_count, aliases, related_concepts
        ORDER BY c.updated_at DESC
        SKIP $offset
        LIMIT $limit
        """

        results = neo4j_client.execute_query(query, params)

        # Query total count / 查询总数
        count_query = f"""
        MATCH (c:Concept)
        {where_clause}
        RETURN count(c) as total
        """
        count_result = neo4j_client.execute_query(
            count_query, params
        )
        total = count_result[0]["total"] if count_result else 0

        # Build response / 构建响应
        cards = []
        for record in results:
            concept = record["c"]
            cards.append(
                KnowledgeCardResponse(
                    id=concept.get("name"),
                    name=concept.get("name"),
                    description=concept.get("description"),
                    domain=concept.get("domain"),
                    category=concept.get("category"),
                    importance=concept.get("importance"),
                    tags=concept.get("tags", []),
                    aliases=record.get("aliases", []),
                    related_concepts=record.get(
                        "related_concepts", []
                    ),
                    attributes={},
                    created_at=_format_timestamp(
                        concept.get("created_at")
                    ),
                    updated_at=_format_timestamp(
                        concept.get("updated_at")
                    ),
                    connection_count=record.get("conn_count", 0),
                )
            )

        return KnowledgeCardListResponse(cards=cards, total=total)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询知识卡片失败: {str(e)}",
        )


@router.get("/{card_id}", response_model=KnowledgeCardResponse)
async def get_knowledge_card(card_id: str):
    """
    Get a single knowledge card by ID (concept name).
    获取单个知识卡片的详细信息。

    GET /knowledge-cards/{card_id}

    Args:
        card_id:  Card ID (concept name) / 卡片 ID（概念名称）

    Returns:
        KnowledgeCardResponse with full card details / 完整的卡片详情

    Raises:
        404: If card not found / 卡片不存在
    """
    try:
        result = neo4j_client.execute_query(
            """
            MATCH (c:Concept {name: $name})
            OPTIONAL MATCH (c)-[r]-()
            WITH c, count(r) as conn_count
            OPTIONAL MATCH (a:Alias)-[r_alias]->(c)
            WITH c, conn_count, collect(a.name) as aliases
            OPTIONAL MATCH (c)-[r_rel]->(related:Concept)
            WITH c, conn_count, aliases,
                collect(related.name) as related_concepts
            RETURN c, conn_count, aliases, related_concepts
            """,
            {"name": card_id},
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"知识卡片 '{card_id}' 不存在",
            )

        record = result[0]
        concept = record["c"]

        return KnowledgeCardResponse(
            id=concept.get("name"),
            name=concept.get("name"),
            description=concept.get("description"),
            domain=concept.get("domain"),
            category=concept.get("category"),
            importance=concept.get("importance"),
            tags=concept.get("tags", []),
            aliases=record.get("aliases", []),
            related_concepts=record.get("related_concepts", []),
            attributes={},
            created_at=_format_timestamp(
                concept.get("created_at")
            ),
            updated_at=_format_timestamp(
                concept.get("updated_at")
            ),
            connection_count=record.get("conn_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询知识卡片失败: {str(e)}",
        )


@router.put("/{card_id}", response_model=KnowledgeCardResponse)
async def update_knowledge_card(
    card_id: str, card: KnowledgeCardUpdate
):
    """
    Update a knowledge card by ID.
    更新指定知识卡片。

    PUT /knowledge-cards/{card_id}

    All fields in the request body are optional — only provided fields
    will be updated. Aliases and related_concepts are replaced entirely
    (not merged).

    Args:
        card_id:  Card ID (concept name) / 卡片 ID
        card:     Update data / 更新内容

    Returns:
        Updated KnowledgeCardResponse / 更新后的知识卡片

    Raises:
        404: If card not found / 卡片不存在
    """
    try:
        # Check existence / 检查是否存在
        existing = neo4j_client.execute_query(
            "MATCH (c:Concept {name: $name}) RETURN c",
            {"name": card_id},
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"知识卡片 '{card_id}' 不存在",
            )

        # Build update properties / 构建更新属性
        update_props = {}
        if card.name is not None:
            update_props["name"] = card.name
        if card.description is not None:
            update_props["description"] = card.description
        if card.domain is not None:
            update_props["domain"] = card.domain
        if card.category is not None:
            update_props["category"] = card.category
        if card.importance is not None:
            update_props["importance"] = card.importance
        if card.tags is not None:
            update_props["tags"] = card.tags
        if card.attributes is not None:
            update_props.update(card.attributes)

        update_props["updated_at"] = datetime.utcnow().isoformat()

        # Update concept node / 更新概念节点
        neo4j_client.execute_query(
            """
            MATCH (c:Concept {name: $old_name})
            SET c += $properties
            RETURN c
            """,
            {
                "old_name": card_id,
                "properties": update_props,
            },
        )

        # Update aliases / 更新别名
        if card.aliases is not None:
            # Delete old aliases / 删除旧别名
            neo4j_client.execute_query(
                """
                MATCH (c:Concept {name: $name})
                OPTIONAL MATCH (c)<-[r]-(a:Alias)
                DETACH DELETE a
                """,
                {"name": card.name or card_id},
            )

            # Create new aliases / 创建新别名
            for alias in card.aliases:
                neo4j_client.execute_query(
                    """
                    MATCH (c:Concept {name: $name})
                    MERGE (a:Alias {name: $alias})
                    MERGE (a)-[:ALIAS_OF]->(c)
                    """,
                    {
                        "name": card.name or card_id,
                        "alias": alias,
                    },
                )

        # Update related concepts / 更新关联概念
        if card.related_concepts is not None:
            # Delete old relations / 删除旧的关系
            neo4j_client.execute_query(
                """
                MATCH (c:Concept {name: $name})-[r]-()
                DELETE r
                """,
                {"name": card.name or card_id},
            )

            # Create new relations / 创建新关系
            for related_name in card.related_concepts:
                neo4j_client.execute_query(
                    """
                    MERGE (c1:Concept {name: $name1})
                    MERGE (c2:Concept {name: $name2})
                    MERGE (c1)-[:RELATED]->(c2)
                    """,
                    {
                        "name1": card.name or card_id,
                        "name2": related_name,
                    },
                )

        # Return updated card / 返回更新后的卡片
        return await get_knowledge_card(card.name or card_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新知识卡片失败: {str(e)}",
        )


@router.delete("/{card_id}")
async def delete_knowledge_card(card_id: str):
    """
    Delete a knowledge card from the graph.
    从图谱中删除知识卡片。

    DELETE /knowledge-cards/{card_id}

    Cascading delete / 级联删除::
        1. Delete all :Alias nodes linked to this concept
        2. DETACH DELETE the :Concept node (removes all relationships)

    Args:
        card_id:  Card ID (concept name) / 卡片 ID

    Returns:
        Dict with success message / 包含成功消息的字典

    Raises:
        404: If card not found / 卡片不存在
    """
    try:
        # Check existence / 检查是否存在
        existing = neo4j_client.execute_query(
            "MATCH (c:Concept {name: $name}) RETURN c",
            {"name": card_id},
        )

        if not existing:
            raise HTTPException(
                status_code=404,
                detail=f"知识卡片 '{card_id}' 不存在",
            )

        # Delete aliases / 删除别名
        neo4j_client.execute_query(
            """
            MATCH (c:Concept {name: $name})<-[r]-(a:Alias)
            DETACH DELETE a
            """,
            {"name": card_id},
        )

        # Delete concept and all its relationships / 删除概念及其所有关系
        neo4j_client.execute_query(
            """
            MATCH (c:Concept {name: $name})
            DETACH DELETE c
            """,
            {"name": card_id},
        )

        return {
            "message": f"知识卡片 '{card_id}' 已删除",
            "success": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除知识卡片失败: {str(e)}",
        )
