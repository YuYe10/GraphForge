"""
Graph Query and Management API Routes
=======================================

知识图谱查询与管理 API 路由，提供图数据查询、可视化和 CRUD 操作。

Provides comprehensive RESTful endpoints for querying and managing the
knowledge graph. Supports graph visualization, Cypher queries, node/edge
CRUD operations, and document/concept subgraph retrieval.

Endpoints / 接口列表::

    # Graph query / 图谱查询
    GET  /graph/visualize           Full graph for visualization / 可视化数据
    GET  /graph/query               Cypher query endpoint / Cypher 查询
    GET  /graph/stats               Graph statistics / 图谱统计

    # Document subgraph / 文档子图
    GET  /graph/documents/{id}/graph  Document knowledge graph / 文档图谱

    # Concept subgraph / 概念子图
    GET  /graph/concepts/{name}/graph  Concept knowledge graph / 概念图谱

    # Node CRUD / 节点 CRUD
    GET    /graph/nodes              List nodes / 获取节点列表
    POST   /graph/nodes              Create node / 创建节点
    GET    /graph/nodes/{id}         Get node / 获取单个节点
    PUT    /graph/nodes/{id}         Update node / 更新节点
    DELETE /graph/nodes/{id}         Delete node / 删除节点

    # Edge CRUD / 边 CRUD
    GET    /graph/edges              List edges / 获取边列表
    POST   /graph/edges              Create edge / 创建边
    PUT    /graph/edges/{s}/{t}/{r}  Update edge / 更新边
    DELETE /graph/edges/{s}/{t}/{r}  Delete edge / 删除边

Type conversion / 类型转换::
    All responses automatically convert Neo4j-specific types
    (DateTime, Node, Relationship) to JSON-serializable Python types
    via _convert_neo4j_types() and _clean_properties().
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
from infra.neo4j_client import neo4j_client
from models.graph import (
    GraphQuery,
    GraphResponse,
    Node,
    Edge,
    NodeCreate,
    NodeUpdate,
    EdgeCreate,
    EdgeUpdate,
)

router = APIRouter(prefix="/graph", tags=["graph"])


def _clean_properties(props: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean property values to ensure JSON serializability.
    清理属性值以确保可 JSON 序列化。

    Converts datetime objects (Python datetime, Neo4j DateTime) to
    ISO 8601 format strings for compatibility with JSON serialization.

    Args:
        props:  Raw properties dict / 原始属性字典

    Returns:
        Cleaned properties dict with ISO strings / 清理后的属性字典
    """
    clean_props = {}
    for k, v in props.items():
        if hasattr(v, 'isoformat'):
            # Python datetime/date/time objects
            clean_props[k] = v.isoformat()
        elif hasattr(v, 'to_native'):
            # Neo4j DateTime objects
            native_val = v.to_native()
            clean_props[k] = (
                native_val.isoformat()
                if hasattr(native_val, 'isoformat')
                else str(v)
            )
        else:
            clean_props[k] = v
    return clean_props


@router.get("/visualize")
async def visualize_graph(
    limit: int = Query(
        500, ge=10, le=5000,
        description="Maximum nodes to return / 最大节点数",
    ),
    node_type: Optional[str] = Query(
        None,
        description="Filter by node type "
                    "(Concept, Document, etc) / 按节点类型过滤",
    ),
):
    """
    Get knowledge graph data optimized for frontend visualization.
    获取适合前端可视化的知识图谱数据。

    GET /graph/visualize

    Returns nodes and edges in a format immediately usable by graph
    visualization libraries (e.g., D3.js, vis-network). Each node
    includes a 'degree' field (number of connections).

    Args:
        limit:      Maximum number of relationships to traverse
                   / 最大关系遍历数
        node_type:  Optional filter by Neo4j label / 按标签过滤

    Returns:
        Dict with nodes, edges, and stats
    """
    try:
        # Build query based on filters / 根据筛选条件构建查询
        if node_type:
            query = f"""
            MATCH (n:{node_type})
            OPTIONAL MATCH (n)-[r]->(m)
            WITH n, r, m
            RETURN n, r, m
            LIMIT {limit}
            """
        else:
            query = f"""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            WITH n, r, m
            RETURN n, r, m
            LIMIT {limit}
            """

        results = neo4j_client.execute_query(query)

        # Process results into nodes and edges / 处理结果为节点和边
        nodes_dict: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        for record in results:
            # Process source node / 处理源节点
            if "n" in record and record["n"]:
                node = record["n"]
                node_props = (
                    dict(node) if isinstance(node, dict) else node
                )
                node_props = neo4j_client._convert_neo4j_types(
                    node_props
                )
                labels = (
                    list(node.labels)
                    if hasattr(node, "labels")
                    else []
                )

                node_id = node_props.get("id") or node_props.get(
                    "name"
                )
                if not node_id:
                    node_id = (
                        getattr(node, "element_id", None)
                        or str(id(node))
                    )

                node_id = str(node_id)

                if node_id not in nodes_dict:
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "labels": labels,
                        "type": labels[0] if labels else "Unknown",
                        "label": node_props.get("name")
                        or node_props.get("filename")
                        or node_id,
                        "properties": node_props,
                        "degree": 0,
                    }

            # Process target node / 处理目标节点
            if "m" in record and record["m"]:
                node = record["m"]
                node_props = (
                    dict(node) if isinstance(node, dict) else node
                )
                node_props = neo4j_client._convert_neo4j_types(
                    node_props
                )
                labels = (
                    list(node.labels)
                    if hasattr(node, "labels")
                    else []
                )

                node_id = node_props.get("id") or node_props.get(
                    "name"
                )
                if not node_id:
                    node_id = (
                        getattr(node, "element_id", None)
                        or str(id(node))
                    )

                node_id = str(node_id)

                if node_id not in nodes_dict:
                    nodes_dict[node_id] = {
                        "id": node_id,
                        "labels": labels,
                        "type": labels[0] if labels else "Unknown",
                        "label": node_props.get("name")
                        or node_props.get("filename")
                        or node_id,
                        "properties": node_props,
                        "degree": 0,
                    }

            # Process relationship / 处理关系
            if "r" in record and record["r"]:
                rel = record["r"]
                source_node = record.get("n")
                target_node = record.get("m")

                if source_node and target_node:
                    source_props = (
                        dict(source_node)
                        if isinstance(source_node, dict)
                        else source_node
                    )
                    source_id = source_props.get("id") or source_props.get(
                        "name"
                    )
                    if not source_id:
                        source_id = (
                            getattr(source_node, "element_id", None)
                            or str(id(source_node))
                        )
                    source_id = str(source_id)

                    target_props = (
                        dict(target_node)
                        if isinstance(target_node, dict)
                        else target_node
                    )
                    target_id = target_props.get("id") or target_props.get(
                        "name"
                    )
                    if not target_id:
                        target_id = (
                            getattr(target_node, "element_id", None)
                            or str(id(target_node))
                        )
                    target_id = str(target_id)

                    rel_type = (
                        rel.type
                        if hasattr(rel, "type")
                        else "RELATES_TO"
                    )
                    rel_props = (
                        dict(rel) if isinstance(rel, dict) else rel
                    )
                    rel_props = neo4j_client._convert_neo4j_types(
                        rel_props
                    )

                    edges.append({
                        "id": f"{source_id}_{rel_type}_{target_id}",
                        "source": source_id,
                        "target": target_id,
                        "type": rel_type,
                        "label": rel_type,
                        "properties": rel_props,
                    })

                    # Update degree for both nodes / 更新两端的连接度
                    if source_id in nodes_dict:
                        nodes_dict[source_id]["degree"] += 1
                    if target_id in nodes_dict:
                        nodes_dict[target_id]["degree"] += 1

        nodes = list(nodes_dict.values())

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "types": list(
                    set(n.get("type", "Unknown") for n in nodes)
                ),
            },
        }

    except Exception as e:
        import traceback

        print(f"Error in visualize_graph: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load graph data: {str(e)}",
        )


@router.get("/query", response_model=GraphResponse)
async def query_graph(
    cypher: Optional[str] = Query(
        None,
        description="Cypher query / Cypher 查询语句",
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Query the knowledge graph using Cypher.
    使用 Cypher 查询知识图谱。

    GET /graph/query

    Example queries / 示例查询::

        MATCH (n) RETURN n LIMIT 10
        MATCH (c:Concept) RETURN c LIMIT 20
        MATCH (d:Document)-[:MENTIONS]->(c:Concept) RETURN d, c LIMIT 10

    Args:
        cypher:  Cypher query string (default returns all) / Cypher 查询
        limit:   Maximum results / 最大结果数

    Returns:
        GraphResponse with nodes, edges, and stats
    """
    if not cypher:
        cypher = f"""
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT {limit}
        """

    try:
        results = neo4j_client.execute_query(cypher)

        nodes_dict = {}
        edges = []

        for record in results:
            # Extract nodes / 提取节点
            if "n" in record and record["n"]:
                node = record["n"]
                props = (
                    dict(node)
                    if hasattr(node, "__getitem__")
                    else {}
                )
                labels = (
                    list(node.labels)
                    if hasattr(node, "labels")
                    else []
                )

                node_id = props.get("id") or props.get("name")
                if not node_id:
                    node_id = (
                        getattr(node, "element_id", None)
                        or str(
                            getattr(
                                node, "id", hash(str(node))
                            )
                        )
                    )

                if node_id not in nodes_dict:
                    nodes_dict[node_id] = Node(
                        id=str(node_id),
                        labels=labels,
                        properties=(
                            neo4j_client._convert_neo4j_types(
                                props
                            )
                        ),
                    )

            if "m" in record and record["m"]:
                node = record["m"]
                props = (
                    dict(node)
                    if hasattr(node, "__getitem__")
                    else {}
                )
                labels = (
                    list(node.labels)
                    if hasattr(node, "labels")
                    else []
                )

                node_id = props.get("id") or props.get("name")
                if not node_id:
                    node_id = (
                        getattr(node, "element_id", None)
                        or str(
                            getattr(
                                node, "id", hash(str(node))
                            )
                        )
                    )

                if node_id not in nodes_dict:
                    nodes_dict[node_id] = Node(
                        id=str(node_id),
                        labels=labels,
                        properties=(
                            neo4j_client._convert_neo4j_types(
                                props
                            )
                        ),
                    )

            # Extract relationships / 提取关系
            if "r" in record and record["r"]:
                rel = record["r"]
                source_node = record.get("n")
                target_node = record.get("m")

                if source_node and target_node:
                    source_props = (
                        dict(source_node)
                        if hasattr(source_node, "__getitem__")
                        else {}
                    )
                    source_id = source_props.get("id") or source_props.get(
                        "name"
                    )
                    if not source_id:
                        source_id = (
                            getattr(
                                source_node, "element_id", None
                            )
                            or str(
                                getattr(
                                    source_node,
                                    "id",
                                    hash(str(source_node)),
                                )
                            )
                        )

                    target_props = (
                        dict(target_node)
                        if hasattr(target_node, "__getitem__")
                        else {}
                    )
                    target_id = target_props.get("id") or target_props.get(
                        "name"
                    )
                    if not target_id:
                        target_id = (
                            getattr(
                                target_node, "element_id", None
                            )
                            or str(
                                getattr(
                                    target_node,
                                    "id",
                                    hash(str(target_node)),
                                )
                            )
                        )

                    if source_id and target_id:
                        rel_type = (
                            rel.type
                            if hasattr(rel, "type")
                            else str(rel)
                        )
                        rel_props = (
                            dict(rel)
                            if hasattr(rel, "__getitem__")
                            else {}
                        )

                        edges.append(
                            Edge(
                                source=str(source_id),
                                target=str(target_id),
                                type=rel_type,
                                properties=(
                                    neo4j_client._convert_neo4j_types(
                                        rel_props
                                    )
                                ),
                            )
                        )

        # Build response with cleaned properties
        # 构建响应，清理属性中的 Neo4j 特殊类型
        response_nodes = [
            Node(
                id=node.id,
                labels=node.labels,
                properties=_clean_properties(node.properties),
            )
            for node in nodes_dict.values()
        ]

        response_edges = [
            Edge(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                type=edge.type,
                properties=_clean_properties(edge.properties),
            )
            for edge in edges
        ]

        return GraphResponse(
            nodes=response_nodes,
            edges=response_edges,
            stats={"count": len(results)},
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query error: {str(e)}",
        )


@router.get("/nodes", response_model=List[Node])
async def get_nodes(
    label: Optional[str] = Query(
        None,
        description="Filter by label / 按标签过滤",
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get all nodes, optionally filtered by Neo4j label.
    获取所有节点，可按标签过滤。

    GET /graph/nodes

    Args:
        label:  Node label filter (e.g., "Concept", "Document")
               / 节点标签过滤
        limit:  Maximum nodes to return / 最大返回数

    Returns:
        List of Node objects / 节点对象列表
    """
    if label:
        query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
    else:
        query = "MATCH (n) RETURN n LIMIT $limit"

    results = neo4j_client.execute_query(query, {"limit": limit})

    nodes = []
    for record in results:
        node = record["n"]
        props = (
            dict(node) if hasattr(node, "__getitem__") else {}
        )
        labels = (
            list(node.labels) if hasattr(node, "labels") else []
        )

        node_id = props.get("id") or props.get("name")
        if not node_id:
            node_id = (
                getattr(node, "element_id", None)
                or str(getattr(node, "id", hash(str(node))))
            )

        clean_props = neo4j_client._convert_neo4j_types(props)

        nodes.append(
            Node(
                id=str(node_id),
                labels=labels,
                properties=clean_props,
            )
        )

    return nodes


@router.get("/edges", response_model=List[Edge])
async def get_edges(
    rel_type: Optional[str] = Query(
        None,
        description="Filter by relationship type / 按关系类型过滤",
    ),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Get all relationships, optionally filtered by type.
    获取所有关系，可按类型过滤。

    GET /graph/edges

    Args:
        rel_type:  Relationship type filter / 关系类型过滤
        limit:     Maximum edges to return / 最大返回数

    Returns:
        List of Edge objects / 边对象列表
    """
    if rel_type:
        query = (
            f"MATCH (a)-[r:{rel_type}]->(b) "
            f"RETURN a, r, b LIMIT $limit"
        )
    else:
        query = (
            "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT $limit"
        )

    results = neo4j_client.execute_query(query, {"limit": limit})

    edges = []
    for record in results:
        source_node = record["a"]
        target_node = record["b"]
        rel = record["r"]

        source_props = (
            dict(source_node)
            if hasattr(source_node, "__getitem__")
            else {}
        )
        source_id = source_props.get("id") or source_props.get(
            "name"
        )
        if not source_id:
            source_id = (
                getattr(source_node, "element_id", None)
                or str(
                    getattr(
                        source_node,
                        "id",
                        hash(str(source_node)),
                    )
                )
            )

        target_props = (
            dict(target_node)
            if hasattr(target_node, "__getitem__")
            else {}
        )
        target_id = target_props.get("id") or target_props.get(
            "name"
        )
        if not target_id:
            target_id = (
                getattr(target_node, "element_id", None)
                or str(
                    getattr(
                        target_node,
                        "id",
                        hash(str(target_node)),
                    )
                )
            )

        if source_id and target_id:
            rel_type_str = (
                rel.type if hasattr(rel, "type") else str(rel)
            )
            rel_props = (
                dict(rel)
                if hasattr(rel, "__getitem__")
                else {}
            )

            clean_rel_props = (
                neo4j_client._convert_neo4j_types(rel_props)
            )

            edges.append(
                Edge(
                    source=str(source_id),
                    target=str(target_id),
                    type=rel_type_str,
                    properties=clean_rel_props,
                )
            )

    return edges


@router.get(
    "/documents/{document_id}/graph",
    response_model=GraphResponse,
)
async def get_document_graph(
    document_id: str,
    depth: int = Query(
        2, ge=1, le=5,
        description="Relationship depth / 关系深度",
    ),
):
    """
    Get the knowledge graph for a specific document.
    获取指定文档的知识图谱。

    GET /graph/documents/{document_id}/graph

    Retrieves all nodes and relationships connected to a document
    up to the specified depth. Auto-marks document as "completed".

    Args:
        document_id:  Document ID / 文档 ID
        depth:        Traversal depth (1-5) / 遍历深度

    Returns:
        GraphResponse with document-centered subgraph
    """
    doc_check = neo4j_client.execute_query(
        "MATCH (d:Document {id: $doc_id}) RETURN d",
        {"doc_id": document_id},
    )

    if not doc_check:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    query = f"""
    MATCH (d:Document {{id: $doc_id}})
    OPTIONAL MATCH path = (d)-[*1..{depth}]-(n)
    WITH d, n, relationships(path) as rels
    LIMIT 300
    RETURN d, n, rels
    """

    results = neo4j_client.execute_query(
        query, {"doc_id": document_id}
    )

    nodes_dict = {}
    edges = []

    for record in results:
        if "d" in record and record["d"]:
            doc_node = record["d"]
            doc_props = (
                dict(doc_node)
                if hasattr(doc_node, "__getitem__")
                else {}
            )
            doc_labels = (
                list(doc_node.labels)
                if hasattr(doc_node, "labels")
                else ["Document"]
            )

            doc_id_val = doc_props.get("id")
            if not doc_id_val:
                doc_id_val = (
                    getattr(doc_node, "element_id", None)
                    or str(
                        getattr(
                            doc_node,
                            "id",
                            hash(str(doc_node)),
                        )
                    )
                )

            if doc_id_val not in nodes_dict:
                nodes_dict[doc_id_val] = Node(
                    id=str(doc_id_val),
                    labels=doc_labels,
                    properties=(
                        neo4j_client._convert_neo4j_types(
                            doc_props
                        )
                    ),
                )

        if "n" in record and record["n"]:
            node = record["n"]
            props = (
                dict(node)
                if hasattr(node, "__getitem__")
                else {}
            )
            labels = (
                list(node.labels)
                if hasattr(node, "labels")
                else ["Concept"]
            )

            node_id = props.get("id") or props.get("name")
            if not node_id:
                node_id = (
                    getattr(node, "element_id", None)
                    or str(
                        getattr(
                            node, "id", hash(str(node))
                        )
                    )
                )

            if node_id not in nodes_dict:
                nodes_dict[node_id] = Node(
                    id=str(node_id),
                    labels=labels,
                    properties=(
                        neo4j_client._convert_neo4j_types(props)
                    ),
                )

        if "rels" in record and record["rels"]:
            for rel in record["rels"]:
                if hasattr(rel, "start_node") and hasattr(
                    rel, "end_node"
                ):
                    start_props = (
                        dict(rel.start_node)
                        if hasattr(
                            rel.start_node, "__getitem__"
                        )
                        else {}
                    )
                    source_id = start_props.get("id") or start_props.get(
                        "name"
                    )
                    if not source_id:
                        source_id = (
                            getattr(
                                rel.start_node,
                                "element_id",
                                None,
                            )
                            or str(
                                getattr(
                                    rel.start_node,
                                    "id",
                                    hash(str(rel.start_node)),
                                )
                            )
                        )

                    end_props = (
                        dict(rel.end_node)
                        if hasattr(rel.end_node, "__getitem__")
                        else {}
                    )
                    target_id = end_props.get("id") or end_props.get(
                        "name"
                    )
                    if not target_id:
                        target_id = (
                            getattr(
                                rel.end_node,
                                "element_id",
                                None,
                            )
                            or str(
                                getattr(
                                    rel.end_node,
                                    "id",
                                    hash(str(rel.end_node)),
                                )
                            )
                        )

                    rel_type = (
                        rel.type
                        if hasattr(rel, "type")
                        else "RELATES_TO"
                    )
                    rel_props = (
                        dict(rel)
                        if hasattr(rel, "__getitem__")
                        else {}
                    )

                    edges.append(
                        Edge(
                            source=str(source_id),
                            target=str(target_id),
                            type=rel_type,
                            properties=(
                                neo4j_client._convert_neo4j_types(
                                    rel_props
                                )
                            ),
                        )
                    )

    # Mark document as processed (best-effort, non-blocking)
    # 标记文档已处理（尽力而为，不阻塞返回）
    try:
        neo4j_client.mark_document_processed(
            document_id, "completed"
        )
    except Exception:
        pass

    # Clean properties for JSON serialization / 清理属性以支持 JSON 序列化
    response_nodes = [
        Node(
            id=node.id,
            labels=node.labels,
            properties=_clean_properties(node.properties),
        )
        for node in nodes_dict.values()
    ]

    response_edges = [
        Edge(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            type=edge.type,
            properties=_clean_properties(edge.properties),
        )
        for edge in edges
    ]

    return GraphResponse(
        nodes=response_nodes,
        edges=response_edges,
        stats={
            "count": len(response_nodes),
            "edges": len(response_edges),
        },
    )


@router.get(
    "/concepts/{concept_name}/graph",
    response_model=GraphResponse,
)
async def get_concept_graph(
    concept_name: str,
    depth: int = Query(
        2, ge=1, le=5,
        description="Relationship depth / 关系深度",
    ),
):
    """
    Get the knowledge graph centered on a specific concept.
    获取以指定概念为中心的知识图谱。

    GET /graph/concepts/{concept_name}/graph

    Retrieves all nodes and relationships connected to a concept
    up to the specified depth. Useful for exploring related concepts.

    Args:
        concept_name:  Concept name / 概念名称
        depth:         Traversal depth (1-5) / 遍历深度

    Returns:
        GraphResponse with concept-centered subgraph

    Raises:
        404: If concept not found / 概念不存在
    """
    concept_check = neo4j_client.execute_query(
        "MATCH (c:Concept {name: $name}) RETURN c",
        {"name": concept_name},
    )

    if not concept_check:
        raise HTTPException(
            status_code=404,
            detail="Concept not found",
        )

    query = f"""
    MATCH (c:Concept {{name: $name}})
    MATCH path = (c)-[*1..{depth}]-(n)
    WITH c, n, relationships(path) as rels
    RETURN c, n, rels
    LIMIT 1000
    """

    results = neo4j_client.execute_query(
        query, {"name": concept_name}
    )

    nodes_dict = {}
    edges = []

    for record in results:
        if "c" in record and record["c"]:
            concept_node = record["c"]
            concept_props = (
                dict(concept_node)
                if hasattr(concept_node, "__getitem__")
                else {}
            )
            concept_labels = (
                list(concept_node.labels)
                if hasattr(concept_node, "labels")
                else ["Concept"]
            )

            concept_id = concept_props.get("name") or concept_props.get(
                "id"
            )
            if not concept_id:
                concept_id = (
                    getattr(concept_node, "element_id", None)
                    or str(
                        getattr(
                            concept_node,
                            "id",
                            hash(str(concept_node)),
                        )
                    )
                )

            if concept_id not in nodes_dict:
                nodes_dict[concept_id] = Node(
                    id=str(concept_id),
                    labels=concept_labels,
                    properties=concept_props,
                )

        if "n" in record and record["n"]:
            node = record["n"]
            props = (
                dict(node)
                if hasattr(node, "__getitem__")
                else {}
            )
            labels = (
                list(node.labels)
                if hasattr(node, "labels")
                else []
            )

            node_id = props.get("id") or props.get("name")
            if not node_id:
                node_id = (
                    getattr(node, "element_id", None)
                    or str(
                        getattr(
                            node, "id", hash(str(node))
                        )
                    )
                )

            if node_id not in nodes_dict:
                nodes_dict[node_id] = Node(
                    id=str(node_id),
                    labels=labels,
                    properties=(
                        neo4j_client._convert_neo4j_types(props)
                    ),
                )

        if "rels" in record and record["rels"]:
            for rel in record["rels"]:
                if hasattr(rel, "start_node") and hasattr(
                    rel, "end_node"
                ):
                    start_props = (
                        dict(rel.start_node)
                        if hasattr(
                            rel.start_node, "__getitem__"
                        )
                        else {}
                    )
                    source_id = start_props.get("id") or start_props.get(
                        "name"
                    )
                    if not source_id:
                        source_id = (
                            getattr(
                                rel.start_node,
                                "element_id",
                                None,
                            )
                            or str(
                                getattr(
                                    rel.start_node,
                                    "id",
                                    hash(str(rel.start_node)),
                                )
                            )
                        )

                    end_props = (
                        dict(rel.end_node)
                        if hasattr(rel.end_node, "__getitem__")
                        else {}
                    )
                    target_id = end_props.get("id") or end_props.get(
                        "name"
                    )
                    if not target_id:
                        target_id = (
                            getattr(
                                rel.end_node,
                                "element_id",
                                None,
                            )
                            or str(
                                getattr(
                                    rel.end_node,
                                    "id",
                                    hash(str(rel.end_node)),
                                )
                            )
                        )

                    rel_type = (
                        rel.type
                        if hasattr(rel, "type")
                        else "RELATES_TO"
                    )
                    rel_props = (
                        dict(rel)
                        if hasattr(rel, "__getitem__")
                        else {}
                    )

                    edges.append(
                        Edge(
                            source=str(source_id),
                            target=str(target_id),
                            type=rel_type,
                            properties=(
                                neo4j_client._convert_neo4j_types(
                                    rel_props
                                )
                            ),
                        )
                    )

    # Clean properties / 清理属性
    response_nodes = [
        Node(
            id=node.id,
            labels=node.labels,
            properties=_clean_properties(node.properties),
        )
        for node in nodes_dict.values()
    ]

    response_edges = [
        Edge(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            type=edge.type,
            properties=_clean_properties(edge.properties),
        )
        for edge in edges
    ]

    return GraphResponse(
        nodes=response_nodes,
        edges=response_edges,
        stats={
            "count": len(response_nodes),
            "edges": len(response_edges),
        },
    )


@router.get("/stats")
async def get_graph_stats():
    """
    Get comprehensive knowledge graph statistics.
    获取全面的知识图谱统计信息。

    GET /graph/stats

    Returns totals and details for graph monitoring:
    - Document, concept, and relationship counts
    - Recently uploaded documents
    - Top concepts by connection count
    - Relationship type distribution

    Returns:
        Dict with totalDocuments, totalConcepts, totalRelations,
        recentDocuments, topConcepts, relationTypes
    """
    try:
        stats_query = """
        MATCH (d:Document)
        WITH count(d) as totalDocs
        OPTIONAL MATCH (c:Concept)
        WITH totalDocs, count(c) as totalConcepts
        OPTIONAL MATCH ()-[r]->()
        RETURN
            totalDocs,
            totalConcepts,
            count(r) as totalRelations
        """
        stats_result = neo4j_client.execute_query(stats_query)

        if not stats_result:
            return {
                "totalDocuments": 0,
                "totalConcepts": 0,
                "totalRelations": 0,
                "recentDocuments": [],
                "topConcepts": [],
                "relationTypes": [],
            }

        stats = stats_result[0]

        # Recent documents / 最近的文档
        recent_docs_query = """
        MATCH (d:Document)
        RETURN d.id as id, d.filename as filename,
               d.created_at as createdAt, d.kind as kind
        ORDER BY d.created_at DESC
        LIMIT 5
        """
        recent_docs = neo4j_client.execute_query(recent_docs_query)

        # Top concepts / 热门概念
        top_concepts_query = """
        MATCH (c:Concept)
        OPTIONAL MATCH (c)-[r]-()
        WITH c, count(r) as connections
        RETURN c.name as name, c.domain as domain, connections
        ORDER BY connections DESC
        LIMIT 10
        """
        top_concepts = neo4j_client.execute_query(
            top_concepts_query
        )

        # Relation type distribution / 关系类型分布
        relation_types_query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        relation_types = neo4j_client.execute_query(
            relation_types_query
        )

        return {
            "totalDocuments": stats.get("totalDocs", 0),
            "totalConcepts": stats.get("totalConcepts", 0),
            "totalRelations": stats.get("totalRelations", 0),
            "recentDocuments": [
                {
                    "id": doc.get("id"),
                    "filename": doc.get("filename"),
                    "createdAt": doc.get("createdAt"),
                    "kind": doc.get("kind"),
                }
                for doc in recent_docs
            ],
            "topConcepts": [
                {
                    "name": concept.get("name"),
                    "domain": concept.get("domain"),
                    "connections": concept.get("connections", 0),
                }
                for concept in top_concepts
            ],
            "relationTypes": [
                {
                    "type": rt.get("type"),
                    "count": rt.get("count", 0),
                }
                for rt in relation_types
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}",
        )


# ══════════════════════════════════════════════════════════════════
# Node CRUD Operations / 节点 CRUD 操作
# ══════════════════════════════════════════════════════════════════


@router.post("/nodes", response_model=Node, status_code=201)
async def create_node(node_data: NodeCreate = Body(...)):
    """
    Create a new graph node.
    创建新的图节点。

    POST /graph/nodes

    Auto-generates: id (UUID4), created_at timestamp.

    Args:
        node_data:  Node labels and properties / 节点标签和属性

    Returns:
        Created Node object / 创建的节点

    Raises:
        500: If creation fails / 创建失败
    """
    try:
        import uuid
        from datetime import datetime

        if "id" not in node_data.properties:
            node_data.properties["id"] = str(uuid.uuid4())

        if "created_at" not in node_data.properties:
            node_data.properties["created_at"] = (
                datetime.now().isoformat()
            )

        labels_str = ":".join(node_data.labels)
        props_dict = node_data.properties

        query = f"""
        CREATE (n:{labels_str})
        SET n = $props
        RETURN n
        """

        results = neo4j_client.execute_query(
            query, {"props": props_dict}
        )

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to create node",
            )

        node = results[0]["n"]
        props = (
            dict(node)
            if hasattr(node, "__getitem__")
            else {}
        )
        labels = (
            list(node.labels)
            if hasattr(node, "labels")
            else []
        )

        return Node(
            id=str(props.get("id")),
            labels=labels,
            properties=neo4j_client._convert_neo4j_types(
                props
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create node: {str(e)}",
        )


@router.get("/nodes/{node_id}", response_model=Node)
async def get_node(node_id: str):
    """
    Get a single node by ID.
    获取指定节点。

    GET /graph/nodes/{node_id}

    Searches by both `id` and `name` properties for flexibility.

    Args:
        node_id:  Node ID or name / 节点 ID 或名称

    Returns:
        Node object / 节点对象

    Raises:
        404: If node not found / 节点不存在
    """
    try:
        query = """
        MATCH (n)
        WHERE n.id = $node_id OR n.name = $node_id
        RETURN n
        LIMIT 1
        """

        results = neo4j_client.execute_query(
            query, {"node_id": node_id}
        )

        if not results:
            raise HTTPException(
                status_code=404,
                detail="Node not found",
            )

        node = results[0]["n"]
        props = (
            dict(node)
            if hasattr(node, "__getitem__")
            else {}
        )
        labels = (
            list(node.labels)
            if hasattr(node, "labels")
            else []
        )

        return Node(
            id=str(
                props.get("id")
                or props.get("name")
                or node_id
            ),
            labels=labels,
            properties=neo4j_client._convert_neo4j_types(
                props
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get node: {str(e)}",
        )


@router.put("/nodes/{node_id}", response_model=Node)
async def update_node(
    node_id: str, node_data: NodeUpdate = Body(...)
):
    """
    Update a node's labels and/or properties.
    更新节点的标签和/或属性。

    PUT /graph/nodes/{node_id}

    Supports:
    - Adding/updating properties (merged via SET +=)
    - Removing specific properties
    - Replacing labels entirely

    Args:
        node_id:   Node ID or name / 节点 ID 或名称
        node_data: Update data / 更新数据

    Returns:
        Updated Node object / 更新后的节点

    Raises:
        404: If node not found / 节点不存在
    """
    try:
        from datetime import datetime

        # Check existence / 检查是否存在
        check_query = """
        MATCH (n)
        WHERE n.id = $node_id OR n.name = $node_id
        RETURN n
        LIMIT 1
        """
        check_results = neo4j_client.execute_query(
            check_query, {"node_id": node_id}
        )

        if not check_results:
            raise HTTPException(
                status_code=404,
                detail="Node not found",
            )

        # Build update query / 构建更新查询
        params = {"node_id": node_id}
        query_parts = []

        if node_data.labels:
            labels_str = ":".join(node_data.labels)
            query_parts.append(f"""
                MATCH (n)
                WHERE n.id = $node_id OR n.name = $node_id
                REMOVE n:{":".join(
                    list(check_results[0]["n"].labels)
                )}
                SET n:{labels_str}
            """)
        else:
            query_parts.append(f"""
                MATCH (n)
                WHERE n.id = $node_id OR n.name = $node_id
            """)

        if node_data.properties:
            node_data.properties["updated_at"] = (
                datetime.now().isoformat()
            )
            params["props"] = node_data.properties
            query_parts.append("SET n += $props")

        if node_data.remove_properties:
            for prop in node_data.remove_properties:
                query_parts.append(f"REMOVE n.{prop}")

        query_parts.append("RETURN n")
        query = "\n".join(query_parts)

        results = neo4j_client.execute_query(query, params)

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to update node",
            )

        node = results[0]["n"]
        props = (
            dict(node)
            if hasattr(node, "__getitem__")
            else {}
        )
        labels = (
            list(node.labels)
            if hasattr(node, "labels")
            else []
        )

        return Node(
            id=str(
                props.get("id")
                or props.get("name")
                or node_id
            ),
            labels=labels,
            properties=neo4j_client._convert_neo4j_types(
                props
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update node: {str(e)}",
        )


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(
    node_id: str,
    force: bool = Query(
        False,
        description="Force delete with relationships "
                    "/ 强制删除（包括关系）",
    ),
):
    """
    Delete a node from the graph.
    从图谱中删除节点。

    DELETE /graph/nodes/{node_id}

    Args:
        node_id:  Node ID or name / 节点 ID 或名称
        force:    If True, also delete all relationships
                 / 如果为 True，同时删除所有关系

    Returns:
        204 No Content

    Raises:
        400: If node has relationships and force=False
        404: If node not found
    """
    try:
        check_query = """
        MATCH (n)
        WHERE n.id = $node_id OR n.name = $node_id
        RETURN n
        LIMIT 1
        """
        check_results = neo4j_client.execute_query(
            check_query, {"node_id": node_id}
        )

        if not check_results:
            raise HTTPException(
                status_code=404,
                detail="Node not found",
            )

        if not force:
            rel_check_query = """
            MATCH (n)-[r]-()
            WHERE n.id = $node_id OR n.name = $node_id
            RETURN count(r) as rel_count
            """
            rel_results = neo4j_client.execute_query(
                rel_check_query, {"node_id": node_id}
            )

            if rel_results and rel_results[0].get("rel_count", 0) > 0:
                raise HTTPException(
                    status_code=400,
                    detail="Node has relationships. "
                           "Use force=true to delete "
                           "with relationships.",
                )

        if force:
            delete_query = """
            MATCH (n)
            WHERE n.id = $node_id OR n.name = $node_id
            DETACH DELETE n
            """
        else:
            delete_query = """
            MATCH (n)
            WHERE n.id = $node_id OR n.name = $node_id
            DELETE n
            """

        neo4j_client.execute_query(
            delete_query, {"node_id": node_id}
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete node: {str(e)}",
        )


# ══════════════════════════════════════════════════════════════════
# Edge (Relationship) CRUD Operations / 边（关系）CRUD 操作
# ══════════════════════════════════════════════════════════════════


@router.post("/edges", response_model=Edge, status_code=201)
async def create_edge(edge_data: EdgeCreate = Body(...)):
    """
    Create a new relationship between two nodes.
    在两个节点之间创建新关系。

    POST /graph/edges

    Auto-generates created_at timestamp and edge ID.

    Args:
        edge_data:  Source, target, type, and properties / 源、目标、类型和属性

    Returns:
        Created Edge object / 创建的关系

    Raises:
        404: If source or target node not found / 源或目标节点不存在
    """
    try:
        from datetime import datetime

        # Verify both nodes exist / 验证两个节点都存在
        check_query = """
        MATCH (s)
        WHERE s.id = $source_id OR s.name = $source_id
        MATCH (t)
        WHERE t.id = $target_id OR t.name = $target_id
        RETURN s, t
        """
        check_results = neo4j_client.execute_query(
            check_query,
            {
                "source_id": edge_data.source,
                "target_id": edge_data.target,
            },
        )

        if not check_results:
            raise HTTPException(
                status_code=404,
                detail="Source or target node not found",
            )

        props = edge_data.properties.copy()
        if "created_at" not in props:
            props["created_at"] = datetime.now().isoformat()

        query = f"""
        MATCH (s)
        WHERE s.id = $source_id OR s.name = $source_id
        MATCH (t)
        WHERE t.id = $target_id OR t.name = $target_id
        CREATE (s)-[r:{edge_data.type}]->(t)
        SET r = $props
        RETURN s, r, t
        """

        results = neo4j_client.execute_query(
            query,
            {
                "source_id": edge_data.source,
                "target_id": edge_data.target,
                "props": props,
            },
        )

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to create relationship",
            )

        rel = results[0]["r"]
        source_node = results[0]["s"]
        target_node = results[0]["t"]

        source_props = (
            dict(source_node)
            if hasattr(source_node, "__getitem__")
            else {}
        )
        source_id = source_props.get("id") or source_props.get(
            "name"
        ) or edge_data.source

        target_props = (
            dict(target_node)
            if hasattr(target_node, "__getitem__")
            else {}
        )
        target_id = target_props.get("id") or target_props.get(
            "name"
        ) or edge_data.target

        rel_type = (
            rel.type if hasattr(rel, "type") else edge_data.type
        )
        rel_props = (
            dict(rel)
            if hasattr(rel, "__getitem__")
            else {}
        )

        edge_id = f"{source_id}-{rel_type}-{target_id}"

        return Edge(
            id=edge_id,
            source=str(source_id),
            target=str(target_id),
            type=rel_type,
            properties=neo4j_client._convert_neo4j_types(
                rel_props
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create relationship: {str(e)}",
        )


@router.put(
    "/edges/{source_id}/{target_id}/{rel_type}",
    response_model=Edge,
)
async def update_edge(
    source_id: str,
    target_id: str,
    rel_type: str,
    edge_data: EdgeUpdate = Body(...),
):
    """
    Update a relationship's type and/or properties.
    更新关系类型和/或属性。

    PUT /graph/edges/{source_id}/{target_id}/{rel_type}

    Supports:
    - Updating properties (merged via SET +=)
    - Removing specific properties
    - Changing relationship type (creates new, deletes old)

    Args:
        source_id:  Source node ID / 源节点 ID
        target_id:  Target node ID / 目标节点 ID
        rel_type:   Current relationship type / 当前关系类型
        edge_data:  Update data / 更新数据

    Returns:
        Updated Edge object / 更新后的关系

    Raises:
        404: If relationship not found / 关系不存在
    """
    try:
        from datetime import datetime

        check_query = f"""
        MATCH (s)-[r:{rel_type}]->(t)
        WHERE (s.id = $source_id OR s.name = $source_id)
          AND (t.id = $target_id OR t.name = $target_id)
        RETURN r
        LIMIT 1
        """
        check_results = neo4j_client.execute_query(
            check_query,
            {
                "source_id": source_id,
                "target_id": target_id,
            },
        )

        if not check_results:
            raise HTTPException(
                status_code=404,
                detail="Relationship not found",
            )

        params = {"source_id": source_id, "target_id": target_id}
        updates = []

        if edge_data.properties:
            edge_data.properties["updated_at"] = (
                datetime.now().isoformat()
            )
            params["props"] = edge_data.properties
            updates.append("SET r += $props")

        if edge_data.remove_properties:
            for prop in edge_data.remove_properties:
                updates.append(f"REMOVE r.{prop}")

        # Handle type change (requires recreating the relationship)
        # 处理类型变更（需要重建关系）
        if edge_data.type and edge_data.type != rel_type:
            query = f"""
            MATCH (s)-[r:{rel_type}]->(t)
            WHERE (s.id = $source_id OR s.name = $source_id)
              AND (t.id = $target_id OR t.name = $target_id)
            WITH s, t, properties(r) as props
            DELETE r
            CREATE (s)-[new_r:{edge_data.type}]->(t)
            SET new_r = props
            {" ".join(updates)
                .replace("r.", "new_r.")
                .replace("r +=", "new_r +=")}
            RETURN s, new_r as r, t
            """
        else:
            query = f"""
            MATCH (s)-[r:{rel_type}]->(t)
            WHERE (s.id = $source_id OR s.name = $source_id)
              AND (t.id = $target_id OR t.name = $target_id)
            {" ".join(updates)}
            RETURN s, r, t
            """

        results = neo4j_client.execute_query(query, params)

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to update relationship",
            )

        rel = results[0]["r"]
        source_node = results[0]["s"]
        target_node = results[0]["t"]

        source_props = (
            dict(source_node)
            if hasattr(source_node, "__getitem__")
            else {}
        )
        actual_source_id = source_props.get("id") or source_props.get(
            "name"
        ) or source_id

        target_props = (
            dict(target_node)
            if hasattr(target_node, "__getitem__")
            else {}
        )
        actual_target_id = target_props.get("id") or target_props.get(
            "name"
        ) or target_id

        rel_type_actual = (
            rel.type
            if hasattr(rel, "type")
            else (edge_data.type or rel_type)
        )
        rel_props = (
            dict(rel)
            if hasattr(rel, "__getitem__")
            else {}
        )

        edge_id = (
            f"{actual_source_id}-"
            f"{rel_type_actual}-"
            f"{actual_target_id}"
        )

        return Edge(
            id=edge_id,
            source=str(actual_source_id),
            target=str(actual_target_id),
            type=rel_type_actual,
            properties=neo4j_client._convert_neo4j_types(
                rel_props
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update relationship: {str(e)}",
        )


@router.delete(
    "/edges/{source_id}/{target_id}/{rel_type}",
    status_code=204,
)
async def delete_edge(
    source_id: str, target_id: str, rel_type: str
):
    """
    Delete a relationship.
    删除关系。

    DELETE /graph/edges/{source_id}/{target_id}/{rel_type}

    Args:
        source_id:  Source node ID / 源节点 ID
        target_id:  Target node ID / 目标节点 ID
        rel_type:   Relationship type / 关系类型

    Returns:
        204 No Content

    Raises:
        404: If relationship not found / 关系不存在
    """
    try:
        check_query = f"""
        MATCH (s)-[r:{rel_type}]->(t)
        WHERE (s.id = $source_id OR s.name = $source_id)
          AND (t.id = $target_id OR t.name = $target_id)
        RETURN r
        LIMIT 1
        """
        check_results = neo4j_client.execute_query(
            check_query,
            {
                "source_id": source_id,
                "target_id": target_id,
            },
        )

        if not check_results:
            raise HTTPException(
                status_code=404,
                detail="Relationship not found",
            )

        delete_query = f"""
        MATCH (s)-[r:{rel_type}]->(t)
        WHERE (s.id = $source_id OR s.name = $source_id)
          AND (t.id = $target_id OR t.name = $target_id)
        DELETE r
        """

        neo4j_client.execute_query(
            delete_query,
            {
                "source_id": source_id,
                "target_id": target_id,
            },
        )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete relationship: {str(e)}",
        )
