"""
Intelligent Q&A Service using Knowledge Graph
===============================================

智能问答服务，基于知识图谱和 AI 提供智能问答能力。

Provides an intelligent question-answering system that combines knowledge
graph context retrieval with AI-powered response generation. When a user
asks a question, the service:

1. Extracts keywords from the question / 从问题中提取关键词
2. Queries Neo4j for relevant entities and relationships / 查询相关实体和关系
3. Formats the graph data as context / 将图谱数据格式化为上下文
4. Sends the question + context to the AI for answer generation
   / 将问题和上下文发送给 AI 生成答案

Architecture / 架构说明::

    User Question
        │
        ▼
    QAService.answer_question()
        │
        ├── query_knowledge_graph()  →  Find relevant entities
        ├── _format_context()        →  Format KG data as text
        ├── Build messages []        →  System + History + Context + Question
        └── AI chat_completion()     →  Generate answer
"""
import json
from typing import Optional, List, Dict, Any
from infra.config import Settings
from infra.ai_providers import get_ai_client
from infra.neo4j_client import neo4j_client


class QAService:
    """
    Service for intelligent Q&A using Neo4j knowledge graph context.
    基于知识图谱的智能问答服务。

    Combines knowledge graph retrieval with AI generation to provide
    contextually grounded answers. The AI is prompted with relevant
    entities and relationships from the graph to ground its responses.

    Attributes:
        settings:       Application settings / 应用配置
        ai_client:      AI provider client instance / AI 客户端实例
        context_limit:  Maximum context characters for the prompt
                       / 上下文最大字符数
    """

    def __init__(self):
        self.settings = Settings()
        self.ai_client = self._initialize_ai_client()
        self.context_limit = 2000  # Character limit for context / 上下文字符限制

    def _initialize_ai_client(self):
        """
        Initialize AI client with the configured provider.
        使用已配置的提供商初始化 AI 客户端。

        Returns:
            AI client instance, or None if initialization fails
            AI 客户端实例，失败时返回 None
        """
        try:
            client = get_ai_client(
                provider=self.settings.ai_provider,
                api_key=self.settings.ai_api_key,
                model=self.settings.ai_model,
                base_url=self.settings.ai_base_url,
            )
            print(
                f"✅ [QA服务] AI客户端初始化成功: "
                f"{self.settings.ai_provider}"
            )
            return client
        except Exception as e:
            print(f"⚠️ [QA服务] AI客户端初始化失败: {e}")
            return None

    def query_knowledge_graph(
        self, question: str, limit: int = 5
    ) -> Dict[str, Any]:
        """
        Query knowledge graph to find relevant entities and relationships.
        查询知识图谱以找到相关的实体和关系。

        Extracts keywords from the question, searches for matching concepts
        in Neo4j (including alias matching), and retrieves their relationships.

        Args:
            question:  User's question / 用户问题
            limit:     Maximum number of relevant nodes to retrieve
                      / 最大检索节点数

        Returns:
            Dict with 'entities' (list of matched entities with relationships)
            and 'keywords' (extracted keywords)
            包含 'entities'（匹配的实体列表）和 'keywords'（关键词）的字典
        """
        try:
            # Extract keywords from question / 提取问题关键词
            keywords = self._extract_keywords(question)

            if not keywords:
                return {"entities": [], "relationships": []}

            # Search for matching concepts (including alias matching)
            # 搜索匹配的概念（包括别名匹配）
            cypher = """
            MATCH (n:Concept)
            WHERE ANY(keyword IN $keywords
                WHERE toLower(n.name) CONTAINS toLower(keyword)
                   OR ANY(alias IN coalesce(n.aliases, [])
                       WHERE toLower(alias) CONTAINS toLower(keyword)))
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
                parameters={"keywords": keywords, "limit": limit},
            )

            entities = []
            for record in results:
                if (
                    record
                    and isinstance(record, dict)
                    and "entity" in record
                ):
                    entity = record["entity"]
                    entity["relationships"] = record.get(
                        "relationships", []
                    )
                    entities.append(entity)

            return {"entities": entities, "keywords": keywords}
        except Exception as e:
            print(f"❌ [QA服务] 知识图谱查询失败: {e}")
            return {"entities": [], "keywords": []}

    def _extract_keywords(self, question: str) -> List[str]:
        """
        Extract meaningful keywords from a question.
        从问题中提取有意义的关键词。

        Uses a simple approach: splits by whitespace/punctuation and filters
        out common stop words in both Chinese and English.

        Args:
            question:  User's question text / 用户问题文本

        Returns:
            List of extracted keywords (max 5) / 提取的关键词列表（最多5个）
        """
        # Stop words in Chinese and English / 中英文停用词
        stop_words = {
            "是什么", "有什么", "怎样", "如何", "什么", "那么",
            "这个", "这是", "的", "了", "和", "是", "在", "有",
            "一个", "中", "到", "会", "被", "以", "与", "为",
            "由", "通过", "从", "使用", "作为", "请问", "请",
            "能否", "可以", "能", "是否", "哪些", "哪个", "哪里",
            "为什么", "什么时候", "什么地方",
            "a", "an", "the", "is", "are",
            "what", "how", "why", "when", "where", "which",
            "can", "could", "would", "should", "might", "may",
            "do", "does", "did",
        }

        # Split into words (simple character-based split for CJK)
        # 分割为词（对中日韩文字使用基于字符的简单分割）
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

        # Filter stop words, keep meaningful terms / 过滤停用词
        keywords = [
            w for w in words if w and len(w) > 1 and w not in stop_words
        ]
        return keywords[:5]  # Max 5 keywords / 最多 5 个关键词

    def _format_context(self, kg_data: Dict[str, Any]) -> str:
        """
        Format knowledge graph data as readable context for AI prompt.
        将知识图谱数据格式化为 AI 可读的上下文文本。

        Each entity is formatted with its name, definition, type, domain,
        and top 3 relationships.

        Args:
            kg_data:  Knowledge graph query results / 知识图谱查询结果

        Returns:
            Formatted context string / 格式化后的上下文字符串
        """
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
                for rel in entity.get("relationships", [])[:3]:
                    rel_str = (
                        f"{rel.get('type', 'RELATED')} "
                        f"{rel.get('target_name', 'Unknown')}"
                    )
                    rel_strs.append(rel_str)
                if rel_strs:
                    entity_str += (
                        f"\n关系: {', '.join(rel_strs)}"
                    )

            context_parts.append(entity_str)

        # Return max 10 entities / 最多返回 10 个实体
        return "\n\n".join(context_parts[:10])

    def answer_question(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_kg: bool = True,
    ) -> Dict[str, Any]:
        """
        Answer a user question using AI with knowledge graph context.
        使用 AI 配合知识图谱上下文回答用户问题。

        Process flow / 处理流程::

            1. If use_kg, query knowledge graph for relevant entities
            2. Build system message with QA guidelines
            3. Append conversation history (last 3 turns)
            4. Append user question with optional KG context
            5. Call AI and return the answer

        Args:
            question:             User's question / 用户问题
            conversation_history: Previous conversation messages
                                / 之前的对话消息
            use_kg:               Whether to use knowledge graph context
                                / 是否使用知识图谱上下文

        Returns:
            Dict with fields: success, answer, used_context,
                             context_snippet, error
            包含 success、answer、used_context、context_snippet、error 的字典
        """
        if not self.ai_client:
            return {
                "success": False,
                "answer": "AI服务未配置",
                "used_context": False,
                "error": "AI客户端未初始化",
            }

        try:
            # Retrieve knowledge graph context / 获取知识图谱上下文
            kg_context = ""
            used_kg = False

            if use_kg:
                kg_data = self.query_knowledge_graph(question)
                if kg_data.get("entities"):
                    kg_context = self._format_context(kg_data)
                    used_kg = True

            # Build message list / 构建消息列表
            messages = []

            # System message with QA guidelines / 带问答指南的系统消息
            system_msg = (
                "你是一个智能问答助手，"
                "专门基于知识图谱回答用户提出的问题。\n\n"
                "请按照以下指导原则：\n"
                "1. 首先参考提供的知识图谱信息来答题\n"
                "2. 如果知识图谱中有相关信息，优先使用这些信息\n"
                "3. 提供清晰、准确和有组织的答案\n"
                "4. 如果信息不足，请说明并给出可能的解释\n"
                "5. 答案应该简明扼要但足够详细\n"
                "6. 使用markdown格式使答案更易阅读"
            )
            messages.append({"role": "system", "content": system_msg})

            # Add conversation history (last 3 rounds max)
            # 添加对话历史（最多最近 3 轮）
            if conversation_history:
                messages.extend(conversation_history[-6:])

            # Build user message with optional KG context
            # 构建含可选 KG 上下文的用户消息
            user_content = question
            if kg_context:
                user_content = (
                    f"【知识图谱信息】\n"
                    f"{kg_context}\n\n"
                    f"【用户问题】\n"
                    f"{question}"
                )

            messages.append(
                {"role": "user", "content": user_content}
            )

            # Call AI / 调用 AI
            answer = self.ai_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )

            return {
                "success": True,
                "answer": answer,
                "used_context": used_kg,
                "context_snippet": (
                    kg_context[:300] if kg_context else None
                ),
                "error": None,
            }

        except Exception as e:
            print(f"❌ [QA服务] 回答问题失败: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "answer": "处理问题时发生错误",
                "used_context": False,
                "error": str(e),
            }


# Global QA service instance / 全局 QA 服务实例
qa_service = QAService()
