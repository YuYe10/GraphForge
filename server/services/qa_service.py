"""Intelligent Q&A service using Neo4j knowledge graph and AI providers."""
import json
from typing import Optional, List, Dict, Any
from infra.config import Settings
from infra.ai_providers import get_ai_client
from infra.neo4j_client import neo4j_client


class QAService:
    """Service for intelligent Q&A using Neo4j knowledge graph."""
    
    def __init__(self):
        self.settings = Settings()
        self.ai_client = self._initialize_ai_client()
        self.context_limit = 2000  # 字符限制
        
    def _initialize_ai_client(self):
        """Initialize AI client with configured provider."""
        try:
            client = get_ai_client(
                provider=self.settings.ai_provider,
                api_key=self.settings.ai_api_key,
                model=self.settings.ai_model,
                base_url=self.settings.ai_base_url
            )
            print(f"✅ [QA服务] AI客户端初始化成功: {self.settings.ai_provider}")
            return client
        except Exception as e:
            print(f"⚠️ [QA服务] AI客户端初始化失败: {e}")
            return None
    
    def query_knowledge_graph(self, question: str, limit: int = 5) -> Dict[str, Any]:
        """
        Query knowledge graph to find relevant entities and relationships.
        
        Args:
            question: User's question
            limit: Maximum number of relevant nodes to retrieve
            
        Returns:
            Dictionary containing relevant knowledge graph data
        """
        try:
            # 提取问题中的关键词（简单方法：分割和清理）
            keywords = self._extract_keywords(question)
            
            if not keywords:
                return {"entities": [], "relationships": []}
            
            # 搜索相关概念
            cypher = """
            MATCH (n:Concept)
            WHERE ANY(keyword IN $keywords WHERE toLower(n.name) CONTAINS toLower(keyword) 
                   OR ANY(alias IN coalesce(n.aliases, []) WHERE toLower(alias) CONTAINS toLower(keyword)))
            WITH n LIMIT $limit
            OPTIONAL MATCH (n)-[r]-(related)
            WITH n, collect({
                type: type(r),
                target_name: related.name,
                target_type: coalesce(related.type, 'Unknown')
            }) AS rels
            RETURN {
                entity: {
                    id: id(n),
                    name: n.name,
                    type: n.type,
                    definition: n.definition,
                    domain: n.domain,
                    aliases: n.aliases
                },
                relationships: rels
            } AS result
            """
            
            results = neo4j_client.execute_query(
                cypher,
                parameters={
                    "keywords": keywords,
                    "limit": limit
                }
            )
            
            entities = []
            for record in results:
                if record and isinstance(record, dict) and "entity" in record:
                    entity = record["entity"]
                    entity["relationships"] = record.get("relationships", [])
                    entities.append(entity)
            
            return {
                "entities": entities,
                "keywords": keywords
            }
        except Exception as e:
            print(f"❌ [QA服务] 知识图谱查询失败: {e}")
            return {"entities": [], "keywords": []}
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract keywords from question."""
        # 简单的关键词提取：去除常见词汇
        stop_words = {
            "是什么", "有什么", "怎样", "如何", "什么", "那么", "这个", "这是",
            "的", "了", "和", "是", "在", "有", "一个", "中", "到", "会",
            "被", "以", "与", "为", "由", "通过", "从", "使用", "作为",
            "请问", "请", "能否", "可以", "能", "是否", "哪些", "哪个", "哪里",
            "为什么", "什么时候", "什么地方", "a", "an", "the", "is", "are",
            "what", "how", "why", "when", "where", "which", "can", "could",
            "would", "should", "might", "may", "do", "does", "did"
        }
        
        # 分割问题为词（简单分割）
        words = []
        current = ""
        for char in question:
            if char in " \n\t，。！？,.:!?":
                if current:
                    words.append(current)
                    current = ""
            else:
                current += char
        if current:
            words.append(current)
        
        # 过滤停用词，保留有意义的词
        keywords = [w for w in words if w and len(w) > 1 and w not in stop_words]
        return keywords[:5]  # 最多5个关键词
    
    def _format_context(self, kg_data: Dict[str, Any]) -> str:
        """Format knowledge graph data as context for AI."""
        context_parts = []
        
        for entity in kg_data.get("entities", []):
            entity_str = f"【{entity.get('name', 'Unknown')}】"
            
            if entity.get("definition"):
                entity_str += f"\n定义: {entity['definition']}"
            
            if entity.get("type"):
                entity_str += f"\n类型: {entity['type']}"
            
            if entity.get("domain"):
                entity_str += f"\n领域: {entity['domain']}"
            
            if entity.get("relationships"):
                rel_strs = []
                for rel in entity.get("relationships", [])[:3]:  # 最多3个关系
                    rel_str = f"{rel.get('type', 'RELATED')} {rel.get('target_name', 'Unknown')}"
                    rel_strs.append(rel_str)
                if rel_strs:
                    entity_str += f"\n关系: {', '.join(rel_strs)}"
            
            context_parts.append(entity_str)
        
        return "\n\n".join(context_parts[:10])  # 最多10个实体
    
    def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_kg: bool = True
    ) -> Dict[str, Any]:
        """
        Answer user's question using AI and knowledge graph.
        
        Args:
            question: User's question
            conversation_history: Previous conversation messages
            use_kg: Whether to use knowledge graph context
            
        Returns:
            Dictionary with answer, used_context, and other metadata
        """
        if not self.ai_client:
            return {
                "success": False,
                "answer": "AI服务未配置",
                "used_context": False,
                "error": "AI客户端未初始化"
            }
        
        try:
            # 获取知识图谱上下文
            kg_context = ""
            used_kg = False
            
            if use_kg:
                kg_data = self.query_knowledge_graph(question)
                if kg_data.get("entities"):
                    kg_context = self._format_context(kg_data)
                    used_kg = True
            
            # 构建消息列表
            messages = []
            
            # 系统消息
            system_msg = """你是一个智能问答助手，专门基于知识图谱回答用户提出的问题。

请按照以下指导原则：
1. 首先参考提供的知识图谱信息来答题
2. 如果知识图谱中有相关信息，优先使用这些信息
3. 提供清晰、准确和有组织的答案
4. 如果信息不足，请说明并给出可能的解释
5. 答案应该简明扼要但足够详细
6. 使用markdown格式使答案更易阅读"""
            
            messages.append({"role": "system", "content": system_msg})
            
            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history[-6:])  # 最多3轮对话
            
            # 用户消息
            user_content = question
            if kg_context:
                user_content = f"""【知识图谱信息】
{kg_context}

【用户问题】
{question}"""
            
            messages.append({"role": "user", "content": user_content})
            
            # 调用AI
            answer = self.ai_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1024
            )
            
            return {
                "success": True,
                "answer": answer,
                "used_context": used_kg,
                "context_snippet": kg_context[:300] if kg_context else None,
                "error": None
            }
        
        except Exception as e:
            print(f"❌ [QA服务] 回答问题失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "answer": "处理问题时发生错误",
                "used_context": False,
                "error": str(e)
            }


# 全局 QA 服务实例
qa_service = QAService()
