"""
阶段 6: 幂等落库 (Graph Service)

将构建结果写入 Neo4j，确保幂等性与证据回溯
"""

import logging
from typing import Dict, Any, List
from infra.neo4j_client import Neo4jClient

logger = logging.getLogger("graphrag.stage6")


class GraphService:
    """
    图谱服务
    
    负责将构建结果写入 Neo4j，支持幂等性与证据回溯
    """
    
    def __init__(self):
        logger.info("GraphService initialized")
        self.neo4j_client = Neo4jClient()
        self.neo4j_client.initialize()
    
    def store_chunk(self, chunk: Dict[str, Any]):
        """
        存储 Chunk 节点
        
        Args:
            chunk: Chunk 数据
        """
        logger.debug("存储 Chunk: %s", chunk.get("id"))
        
        query = """
        MERGE (c:Chunk {id: $id})
        SET c.doc_id = $doc_id,
            c.text = $text,
            c.resolved_text = $resolved_text,
            c.chunk_index = $chunk_index,
            c.section_path = $section_path,
            c.page_num = $page_num,
            c.sentence_ids = $sentence_ids,
            c.sentence_count = $sentence_count,
            c.window_start = $window_start,
            c.window_end = $window_end,
            c.embedding = $embedding,
            c.coreference_aliases = $coreference_aliases,
            c.coref_mode = $coref_mode,
            c.build_version = $build_version,
            c.updated_at = datetime(),
            c.created_at = CASE WHEN c.created_at IS NULL THEN datetime() ELSE c.created_at END
        """
        
        params = {
            "id": chunk.get("id"),
            "doc_id": chunk.get("doc_id"),
            "text": chunk.get("text"),
            "resolved_text": chunk.get("resolved_text"),
            "chunk_index": chunk.get("chunk_index"),
            "section_path": chunk.get("section_path"),
            "page_num": chunk.get("page_num"),
            "sentence_ids": chunk.get("sentence_ids", []),
            "sentence_count": chunk.get("sentence_count", 0),
            "window_start": chunk.get("window_start"),
            "window_end": chunk.get("window_end"),
            "embedding": chunk.get("embedding"),
            "coreference_aliases": chunk.get("coreference_aliases"),
            "coref_mode": chunk.get("coref_mode"),
            "build_version": chunk.get("build_version")
        }
        
        self.neo4j_client.execute_query(query, params)
    
    def store_concept(self, concept: Dict[str, Any]):
        """
        存储 Concept 节点
        
        Args:
            concept: Concept 数据
        """
        logger.debug("存储 Concept: %s", concept.get("id"))
        
        query = """
        MERGE (c:Concept {id: $id})
        SET c.name = $name,
            c.description = $description,
            c.domain = $domain,
            c.aliases = $aliases,
            c.importance = $importance,
            c.frequency = $frequency,
            c.embedding = $embedding,
            c.build_version = $build_version,
            c.updated_at = datetime(),
            c.created_at = CASE WHEN c.created_at IS NULL THEN datetime() ELSE c.created_at END
        """
        
        params = {
            "id": concept.get("id"),
            "name": concept.get("name"),
            "description": concept.get("description"),
            "domain": concept.get("domain"),
            "aliases": concept.get("aliases", []),
            "importance": concept.get("importance"),
            "frequency": concept.get("frequency"),
            "embedding": concept.get("embedding"),
            "build_version": concept.get("build_version")
        }
        
        self.neo4j_client.execute_query(query, params)
    
    def store_claim(self, claim: Dict[str, Any]):
        """
        存储 Claim 节点
        
        Args:
            claim: Claim 数据
        """
        logger.debug("存储 Claim: %s", claim.get("id"))
        
        query = """
        MERGE (cl:Claim {id: $id})
        SET cl.text = $text,
            cl.doc_id = $doc_id,
            cl.chunk_id = $chunk_id,
            cl.sentence_ids = $sentence_ids,
            cl.claim_type = $claim_type,
            cl.confidence = $confidence,
            cl.modality = $modality,
            cl.polarity = $polarity,
            cl.certainty = $certainty,
            cl.evidence_span = $evidence_span,
            cl.section_path = $section_path,
            cl.build_version = $build_version,
            cl.updated_at = datetime(),
            cl.created_at = CASE WHEN cl.created_at IS NULL THEN datetime() ELSE cl.created_at END
        """
        
        params = {
            "id": claim.get("id"),
            "text": claim.get("text"),
            "doc_id": claim.get("doc_id"),
            "chunk_id": claim.get("chunk_id"),
            "sentence_ids": claim.get("sentence_ids", []),
            "claim_type": claim.get("claim_type"),
            "confidence": claim.get("confidence"),
            "modality": claim.get("modality"),
            "polarity": claim.get("polarity"),
            "certainty": claim.get("certainty"),
            "evidence_span": claim.get("evidence_span"),
            "section_path": claim.get("section_path"),
            "build_version": claim.get("build_version")
        }
        
        self.neo4j_client.execute_query(query, params)
    
    def store_relation(self, relation: Dict[str, Any]):
        """
        存储关系
        
        Args:
            relation: 关系数据 {source_id, target_id, type, properties}
        """
        logger.debug("存储关系: %s -%s-> %s", relation.get("source_id"), relation.get("type"), relation.get("target_id"))
        
        query = """
        MATCH (s {id: $source_id}), (t {id: $target_id})
        MERGE (s)-[r:RELATION {id: $rel_id}]->(t)
        SET r.type = $type,
            r.weight = $weight,
            r.confidence = $confidence,
            r.properties = $properties,
            r.updated_at = datetime(),
            r.created_at = CASE WHEN r.created_at IS NULL THEN datetime() ELSE r.created_at END
        """
        
        import json
        # 生成关系 ID
        rel_id = f"{relation.get('source_id')}_{relation.get('type')}_{relation.get('target_id')}"
        
        # 将 properties 转换为 JSON 字符串
        properties_dict = relation.get("properties", {})
        properties_str = json.dumps(properties_dict) if properties_dict else "{}"
        
        params = {
            "source_id": relation.get("source_id"),
            "target_id": relation.get("target_id"),
            "rel_id": rel_id,
            "type": relation.get("type"),
            "weight": relation.get("weight", 1.0),
            "confidence": relation.get("confidence"),
            "properties": properties_str
        }
        
        self.neo4j_client.execute_query(query, params)
    
    def store_with_provenance(
        self,
        node: Dict[str, Any],
        evidence_chunk_id: str,
        doc_id: str,
        section_path: str | None = None,
        sentence_ids: List[str] | None = None
    ):
        """
        存储节点并添加证据回溯
        
        Args:
            node: 节点数据
            evidence_chunk_id: 证据 Chunk ID
            doc_id: 文档 ID
            section_path: 章节路径
            sentence_ids: 句子 ID 列表
        """
        logger.debug("存储节点（带证据）: %s", node.get("id"))
        
        # 确定节点类型
        node_type = node.get("type", "Node")
        
        # 1. 存储节点（使用通用的属性集合）
        store_query = f"""
        MERGE (n:{node_type} {{id: $id}})
        SET n += $properties,
            n.updated_at = datetime(),
            n.created_at = CASE WHEN n.created_at IS NULL THEN datetime() ELSE n.created_at END
        RETURN n
        """
        
        params = {
            "id": node.get("id"),
            "properties": {k: v for k, v in node.items() if k != "id" and k != "type"}
        }
        
        self.neo4j_client.execute_query(store_query, params)
        
        # 2. 创建 EVIDENCE_FROM 关系（连接到证据 Chunk）
        evidence_query = """
        MATCH (n {id: $node_id}), (chunk:Chunk {id: $chunk_id})
        MERGE (n)-[e:EVIDENCE_FROM]->(chunk)
        SET e.doc_id = $doc_id,
            e.section_path = $section_path,
            e.sentence_ids = $sentence_ids,
            e.evidence_type = $evidence_type,
            e.timestamp = datetime(),
            e.created_at = CASE WHEN e.created_at IS NULL THEN datetime() ELSE e.created_at END
        """
        
        evidence_params = {
            "node_id": node.get("id"),
            "chunk_id": evidence_chunk_id,
            "doc_id": doc_id,
            "section_path": section_path,
            "sentence_ids": sentence_ids or [],
            "evidence_type": "EXTRACTED_FROM"
        }
        
        self.neo4j_client.execute_query(evidence_query, evidence_params)


__all__ = ["GraphService"]

