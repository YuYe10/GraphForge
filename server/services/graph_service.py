"""Graph service for ingesting triplets into Neo4j."""
from typing import List, Dict, Any, Optional
from models.document import Triplet
from infra.neo4j_client import neo4j_client


class GraphService:
    """Service for graph operations."""
    
    def ingest_triplets(self, doc_id: str, triplets: List[Triplet], root_topic: Optional[str] = None):
        """
        Ingest triplets into Neo4j graph.
        
        Args:
            doc_id: Document ID
            triplets: List of triplets to ingest
            root_topic: Optional root topic name. If provided, concepts will be linked to topic instead of document.
        """
        print(f"💾 [图谱构建] 开始将 {len(triplets)} 个三元组写入 Neo4j...")
        if root_topic:
            print(f"   📌 主题根节点: {root_topic}")
        
        # Create or get topic root node if provided
        if root_topic:
            neo4j_client.create_or_get_topic(root_topic)
            neo4j_client.link_document_to_topic(doc_id, root_topic)
        
        created_concepts = set()
        created_relationships = 0
        
        for idx, triplet in enumerate(triplets, 1):
            # Ensure concepts exist
            if triplet.subject not in created_concepts:
                neo4j_client.create_concept(triplet.subject)
                created_concepts.add(triplet.subject)
            
            if triplet.object not in created_concepts:
                neo4j_client.create_concept(triplet.object)
                created_concepts.add(triplet.object)
            
            # Create relationship between concepts
            rel_type = triplet.predicate.upper().replace(" ", "_")
            neo4j_client.create_relationship(
                source_id=triplet.subject,
                target_id=triplet.object,
                rel_type=rel_type,
                properties={
                    "confidence": triplet.confidence,
                    "evidence": triplet.evidence,
                    "doc_id": doc_id,
                    "chunk_id": triplet.chunk_id
                }
            )
            created_relationships += 1
            
            # 显示前5个三元组的详细信息
            if idx <= 5:
                print(f"   [{idx}] {triplet.subject} --[{rel_type}]--> {triplet.object} (置信度: {triplet.confidence:.2f})")
            
            # Link concepts to topic root node (if provided) or document (fallback)
            if root_topic:
                # Link to topic root node
                neo4j_client.link_concept_to_topic(
                    concept_name=triplet.subject,
                    topic_name=root_topic,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                    doc_id=doc_id
                )
                
                neo4j_client.link_concept_to_topic(
                    concept_name=triplet.object,
                    topic_name=root_topic,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500],
                    doc_id=doc_id
                )
            elif doc_id:
                # Fallback: link to document (backward compatibility)
                neo4j_client.link_concept_to_document(
                    concept_name=triplet.subject,
                    doc_id=doc_id,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500]
                )
                
                neo4j_client.link_concept_to_document(
                    concept_name=triplet.object,
                    doc_id=doc_id,
                    page=triplet.evidence.get("page"),
                    offset=triplet.evidence.get("offset"),
                    evidence=triplet.evidence.get("text", "")[:500]
                )
        
        if len(triplets) > 5:
            print(f"   ... 还有 {len(triplets) - 5} 个三元组")
        
        print(f"✅ [图谱构建] 完成:")
        print(f"   - 创建/更新概念数: {len(created_concepts)}")
        print(f"   - 创建关系数: {created_relationships}")
    
    def ingest_rich_concepts(self, doc_id: str, concepts: List[Dict[str, Any]], root_topic: Optional[str] = None):
        """
        将AI提取的丰富概念信息写入Neo4j。
        
        Args:
            doc_id: 文档ID
            concepts: 概念列表，包含详细属性
            root_topic: Optional root topic name. If provided, concepts will be linked to topic instead of document.
        """
        print(f"💎 [丰富概念] 开始写入 {len(concepts)} 个增强概念...")
        if root_topic:
            print(f"   📌 主题根节点: {root_topic}")
        
        # Create or get topic root node if provided
        if root_topic:
            neo4j_client.create_or_get_topic(root_topic)
            neo4j_client.link_document_to_topic(doc_id, root_topic)
        
        for idx, concept in enumerate(concepts, 1):
            name = concept.get("name", "")
            if not name:
                continue
            
            # 创建或更新概念，附加丰富的属性
            properties = {
                "description": concept.get("description", ""),
                "domain": concept.get("domain", ""),
                "category": concept.get("category", ""),
                "importance": concept.get("importance", "medium")
            }
            
            # 合并自定义属性
            if concept.get("attributes"):
                properties.update(concept["attributes"])
            
            # 创建概念节点
            neo4j_client.execute_query(
                """
                MERGE (c:Concept {name: $name})
                SET c += $properties
                SET c.updated_at = datetime()
                """,
                {
                    "name": name,
                    "properties": properties
                }
            )
            
            # 处理别名
            aliases = concept.get("aliases", [])
            if aliases:
                for alias in aliases:
                    neo4j_client.execute_query(
                        """
                        MATCH (c:Concept {name: $name})
                        MERGE (a:Alias {name: $alias})
                        MERGE (a)-[:ALIAS_OF]->(c)
                        """,
                        {"name": name, "alias": alias}
                    )
            
            # Link to topic root node (if provided) or document (fallback)
            if root_topic:
                neo4j_client.link_concept_to_topic(
                    concept_name=name,
                    topic_name=root_topic,
                    doc_id=doc_id
                )
            elif doc_id:
                # Fallback: link to document (backward compatibility)
                neo4j_client.link_concept_to_document(
                    concept_name=name,
                    doc_id=doc_id
                )
            
            if idx <= 3:
                print(f"   [{idx}] {name} ({concept.get('category', 'unknown')}) - {concept.get('description', '')[:50]}...")
        
        if len(concepts) > 3:
            print(f"   ... 还有 {len(concepts) - 3} 个概念")
        
        print(f"✅ [丰富概念] 完成")
