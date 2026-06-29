"""
Graph Service — Triplet and Concept Ingestion into Neo4j
=========================================================

图谱服务，负责将抽取的知识三元组和概念写入 Neo4j 图数据库。

Orchestrates the ingestion of extracted knowledge into the Neo4j graph
database. Handles both the traditional triplet pipeline and the AI-powered
rich concept pipeline, with support for topic-based organization.

Ingestion flow / 写入流程::

    Triplets / Concepts
        │
        ├── create_concept()  →  MERGE by name (idempotent)
        │       │
        │       └── add alias nodes if present
        │
        ├── create_relationship()  →  MERGE edge with properties
        │
        └── link_concept_to_topic() or link_concept_to_document()
                │
                └── Create MENTIONS/BELONGS_TO/CONTAINS edges

Key features / 主要特性::
    - Topic-rooted organization (optional) / 主题根节点组织（可选）
    - Fallback document linking (backward compatible) / 文档链接回退（向后兼容）
    - Rich concept metadata (description, domain, category, importance)
    - Idempotent MERGE operations / 幂等 MERGE 操作
"""
from typing import List, Dict, Any, Optional
from models.document import Triplet
from infra.neo4j_client import neo4j_client


class GraphService:
    """
    Service for ingesting triplets and concepts into the Neo4j knowledge graph.
    将三元组和概念写入 Neo4j 知识图谱的服务。

    Provides two main ingestion pipelines:
    - ingest_triplets():     Traditional triplet-based extraction
    - ingest_rich_concepts(): AI-powered extraction with rich metadata

    Both support optional topic-based organization where concepts are linked
    to a root Topic node instead of directly to a Document.
    """

    def ingest_triplets(
        self,
        doc_id: str,
        triplets: List[Triplet],
        root_topic: Optional[str] = None,
    ):
        """
        Ingest triplets into the Neo4j knowledge graph.
        将三元组写入 Neo4j 知识图谱。

        For each triplet:
        1. Ensures subject and object concepts exist (MERGE)
        2. Creates a directed relationship between them
        3. Links concepts to the topic root or document

        Args:
            doc_id:     Document ID / 文档 ID
            triplets:   List of triplets to ingest / 待写入的三元组列表
            root_topic: Optional topic root node name. If provided, concepts
                       will be linked to topic instead of document.
                       / 可选的主题根节点名称
        """
        print(
            f"💾 [图谱构建] 开始将 {len(triplets)} 个三元组"
            f"写入 Neo4j..."
        )
        if root_topic:
            print(f"   📌 主题根节点: {root_topic}")

        # Create topic root node if provided / 如果需要，创建主题根节点
        if root_topic:
            neo4j_client.create_or_get_topic(root_topic)
            neo4j_client.link_document_to_topic(doc_id, root_topic)

        created_concepts = set()
        created_relationships = 0

        for idx, triplet in enumerate(triplets, 1):
            # Ensure concepts exist (idempotent MERGE)
            # 确保概念存在（幂等 MERGE）
            if triplet.subject not in created_concepts:
                neo4j_client.create_concept(triplet.subject)
                created_concepts.add(triplet.subject)

            if triplet.object not in created_concepts:
                neo4j_client.create_concept(triplet.object)
                created_concepts.add(triplet.object)

            # Create relationship between concepts / 创建概念间的关系
            rel_type = triplet.predicate.upper().replace(" ", "_")
            neo4j_client.create_relationship(
                source_id=triplet.subject,
                target_id=triplet.object,
                rel_type=rel_type,
                properties={
                    "confidence": triplet.confidence,
                    "evidence": triplet.evidence,
                    "doc_id": doc_id,
                    "chunk_id": triplet.chunk_id,
                },
            )
            created_relationships += 1

            # Display first 5 triplets for debugging / 显示前5个三元组
            if idx <= 5:
                print(
                    f"   [{idx}] "
                    f"{triplet.subject} "
                    f"--[{rel_type}]--> "
                    f"{triplet.object} "
                    f"(置信度: {triplet.confidence:.2f})"
                )

            # Link concepts to topic root or document
            # 将概念链接到主题根节点或文档
            if root_topic:
                neo4j_client.link_concept_to_topic(
                    concept_name=triplet.subject,
                    topic_name=root_topic,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                    doc_id=doc_id,
                )
                neo4j_client.link_concept_to_topic(
                    concept_name=triplet.object,
                    topic_name=root_topic,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                    doc_id=doc_id,
                )
            elif doc_id:
                # Fallback: link to document (backward compatibility)
                # 回退：链接到文档（向后兼容）
                neo4j_client.link_concept_to_document(
                    concept_name=triplet.subject,
                    doc_id=doc_id,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                )
                neo4j_client.link_concept_to_document(
                    concept_name=triplet.object,
                    doc_id=doc_id,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                )

        if len(triplets) > 5:
            print(
                f"   ... 还有 {len(triplets) - 5} 个三元组"
            )

        print(f"✅ [图谱构建] 完成:")
        print(f"   - 创建/更新概念数: {len(created_concepts)}")
        print(f"   - 创建关系数: {created_relationships}")

    def ingest_rich_concepts(
        self,
        doc_id: str,
        concepts: List[Dict[str, Any]],
        root_topic: Optional[str] = None,
    ):
        """
        Ingest AI-extracted rich concepts with metadata into Neo4j.
        将 AI 提取的丰富概念（含元数据）写入 Neo4j。

        Unlike ingest_triplets, this method handles concepts with extensive
        metadata including descriptions, domains, categories, aliases, and
        custom attributes.

        Args:
            doc_id:     Document ID / 文档 ID
            concepts:   List of rich concept dicts with metadata
                       / 含元数据的丰富概念字典列表
            root_topic: Optional topic root node name / 可选的主题根节点名称
        """
        print(
            f"💎 [丰富概念] 开始写入 {len(concepts)} 个增强概念..."
        )
        if root_topic:
            print(f"   📌 主题根节点: {root_topic}")

        # Create topic root node if provided / 如果需要，创建主题根节点
        if root_topic:
            neo4j_client.create_or_get_topic(root_topic)
            neo4j_client.link_document_to_topic(doc_id, root_topic)

        for idx, concept in enumerate(concepts, 1):
            name = concept.get("name", "")
            if not name:
                continue

            # Build properties with rich metadata / 构建含元数据的属性
            properties = {
                "description": concept.get("description", ""),
                "domain": concept.get("domain", ""),
                "category": concept.get("category", ""),
                "importance": concept.get("importance", "medium"),
            }

            # Merge custom attributes / 合并自定义属性
            if concept.get("attributes"):
                properties.update(concept["attributes"])

            # Create or update concept node (MERGE by name)
            # 创建或更新概念节点（按名称 MERGE）
            neo4j_client.execute_query(
                """
                MERGE (c:Concept {name: $name})
                SET c += $properties
                SET c.updated_at = datetime()
                """,
                {"name": name, "properties": properties},
            )

            # Handle aliases / 处理别名
            aliases = concept.get("aliases", [])
            if aliases:
                for alias in aliases:
                    neo4j_client.execute_query(
                        """
                        MATCH (c:Concept {name: $name})
                        MERGE (a:Alias {name: $alias})
                        MERGE (a)-[:ALIAS_OF]->(c)
                        """,
                        {"name": name, "alias": alias},
                    )

            # Link to topic root or document / 链接到主题或文档
            if root_topic:
                neo4j_client.link_concept_to_topic(
                    concept_name=name,
                    topic_name=root_topic,
                    doc_id=doc_id,
                )
            elif doc_id:
                neo4j_client.link_concept_to_document(
                    concept_name=name, doc_id=doc_id
                )

            if idx <= 3:
                print(
                    f"   [{idx}] {name} "
                    f"({concept.get('category', 'unknown')}) - "
                    f"{concept.get('description', '')[:50]}..."
                )

        if len(concepts) > 3:
            print(f"   ... 还有 {len(concepts) - 3} 个概念")

        print(f"✅ [丰富概念] 完成")
