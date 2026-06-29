"""
AI-Powered Document Segmentation and Knowledge Extraction Service
==================================================================

AI 驱动的文档分析与知识抽取服务。

Provides advanced AI-powered document analysis that goes beyond simple
triplet extraction. The AI Segmenter performs three stages of analysis:

Pipeline stages / 流水线阶段::

    Stage 1: Document Structure Analysis / 文档结构分析
        ─ Identifies themes, domains, key concepts
        ─ User prompt optimization / 用户提示词优化
        ─ Document type and complexity classification

    Stage 2: Rich Knowledge Extraction (per chunk) / 深度知识抽取
        ─ Extracts concepts with metadata (descriptions, categories, aliases)
        ─ Extracts triplets with semantic relationship types
        ─ Generates deep insights and understanding

    Stage 3: Knowledge Fusion / 知识融合
        ─ Concepts are merged into the existing graph
        ─ Rich metadata is preserved on Concept nodes
        ─ Deep insights are returned to the user

Architecture / 架构说明::

    AISegmenter
        │
        ├── optimize_user_prompt()        → Improve user analysis prompts
        ├── analyze_document_structure()   → Stage 1: Document analysis
        └── extract_rich_knowledge()       → Stage 2: Per-chunk extraction
"""
import json
from typing import List, Dict, Any, Optional
from infra.ai_providers import AIProviderFactory, BaseAIClient
from models.document import Chunk, Triplet
from services.config_service import config_service


class AISegmenter:
    """
    AI-powered document analysis and knowledge extraction service.
    AI 驱动的文档分析与知识抽取服务。

    Provides intelligent document analysis capabilities that understand
    document context, extract rich conceptual knowledge, and generate
    deep insights beyond basic triplet extraction.

    This service requires a configured AI provider (throws ValueError
    if none is available).

    Attributes:
        provider:  AI provider name / AI 提供商名称
        client:    AI client instance / AI 客户端实例
        model:     Model name / 模型名称

    Raises:
        ValueError: If AI provider is not configured / 如果未配置 AI 提供商
    """

    def __init__(self):
        """Initialize AI segmenter with the configured AI provider."""
        self.provider = None
        self.client: Optional[BaseAIClient] = None
        self.model = None

        try:
            # Load AI configuration from runtime config
            # 从数据库读取运行时配置
            ai_config = config_service.get_ai_provider_config()
            self.provider = ai_config["provider"]
            api_key = ai_config["api_key"]
            model = ai_config["model"]
            base_url = ai_config["base_url"]

            # Mock mode doesn't need a real API key / Mock 模式不需要 API key
            if self.provider == "mock":
                api_key = api_key or "mock"

            # Create AI client / 创建 AI 客户端
            self.client = AIProviderFactory.create_client(
                provider=self.provider,
                api_key=api_key,
                model=model,
                base_url=base_url,
            )
            self.model = self.client.model

            # Display provider info / 显示提供商信息
            provider_info = AIProviderFactory.get_provider_info(
                self.provider
            )
            provider_name = provider_info.get("name", self.provider)
            print(
                f"✅ AI Segmenter initialized with "
                f"{provider_name} (model: {self.model})"
            )

        except ValueError as e:
            raise ValueError(
                f"Failed to initialize AI segmenter: {str(e)}"
            )

    def optimize_user_prompt(self, user_prompt: str) -> str:
        """
        Optimize a user-provided analysis prompt for better document analysis.
        优化用户提供的分析提示词，使其更适合文档分析。

        Uses an AI-driven meta-prompting approach: sends the user's prompt
        to the AI with instructions to make it more structured, specific,
        and effective for knowledge graph extraction.

        Args:
            user_prompt:  Original user prompt / 用户原始提示词

        Returns:
            Optimized prompt string / 优化后的提示词字符串
        """
        system_prompt = (
            "你是一个专业的知识工程师，擅长优化文档分析提示词。\n\n"
            "你的任务是：\n"
            "1. 理解用户的分析意图和关注点\n"
            "2. 将用户的需求转换为清晰、结构化的分析指令\n"
            "3. 确保优化后的提示词能够引导 AI 提取高质量的知识图谱\n\n"
            "优化原则：\n"
            "- 保留用户的核心关注点和分析目标\n"
            "- 补充必要的结构化要求（如概念、关系、属性等）\n"
            "- 使指令更加明确和可执行\n"
            "- 避免过度复杂，保持简洁有力\n\n"
            "请直接返回优化后的提示词，不要添加额外说明。"
        )

        try:
            response_text = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"请优化以下用户提示词：\n\n{user_prompt}"
                        ),
                    },
                ],
                temperature=0.7,
                max_tokens=500,
            )

            optimized = response_text.strip()
            print(f"\n🔧 [Prompt优化]")
            print(f"   原始: {user_prompt[:100]}...")
            print(f"   优化: {optimized[:100]}...")

            return optimized

        except Exception as e:
            print(
                f"⚠️  Prompt优化失败，使用原始Prompt: {str(e)}"
            )
            return user_prompt

    def analyze_document_structure(
        self,
        chunks: List[Chunk],
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze the overall document structure — Stage 1 of AI analysis.
        分析文档整体结构 — AI 分析的第一阶段。

        Examines a sample of the document (first 3 chunks) to identify:
        - Core themes / 核心主题
        - Knowledge domains / 知识领域
        - Key concepts / 关键概念
        - Document type / 文档类型
        - Complexity level / 难度级别

        Args:
            chunks:      List of document chunks / 文档文本块列表
            user_prompt: Optional user-provided analysis focus
                        / 可选的自定义分析关注点

        Returns:
            Dict with keys: themes, domains, key_concepts,
            document_type, complexity
            包含主题、领域、关键概念、文档类型、难度的字典
        """
        # Sample first 3 chunks for analysis / 取前 3 个块作为样本
        sample_text = "\n\n".join([c.text for c in chunks[:3]])

        base_prompt = (
            "分析这段文档内容，识别其核心主题、关键概念和知识领域。\n\n"
            "请以JSON格式返回：\n"
            '{{\n'
            '    "themes": ["主题1", "主题2", ...],  '
            "// 文档的核心主题（3-5个）\n"
            '    "domains": ["领域1", "领域2", ...],  '
            "// 涉及的知识领域\n"
            '    "key_concepts": ["概念1", "概念2", ...],  '
            "// 最重要的概念（5-10个）\n"
            '    "document_type": "类型",  '
            "// 如：技术文档、学术论文、教程等\n"
            '    "complexity": "难度"  '
            "// 如：入门、中级、高级\n"
            "}}"
        )

        # If user prompt provided, incorporate it / 如果提供了用户提示词，融入分析指令
        if user_prompt:
            analysis_prompt = (
                f"{base_prompt}\n\n用户特别关注：{user_prompt}"
            )
        else:
            analysis_prompt = base_prompt

        try:
            response_text = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是知识图谱专家，擅长分析文档结构和"
                            "识别核心概念。请以JSON格式返回结果。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"{analysis_prompt}\n\n"
                            f"文档内容：\n{sample_text}"
                        ),
                    },
                ],
                temperature=0.3,
                json_mode=True,
            )

            result = json.loads(response_text)
            return result

        except Exception as e:
            print(f"⚠️  文档结构分析失败: {str(e)}")
            return {
                "themes": [],
                "domains": [],
                "key_concepts": [],
                "document_type": "unknown",
                "complexity": "unknown",
            }

    def extract_rich_knowledge(
        self,
        chunk: Chunk,
        document_context: Dict[str, Any],
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extract rich knowledge from a text chunk — Stage 2 of AI analysis.
        从文本块中提取丰富的知识内容 — AI 分析的第二阶段。

        Goes beyond simple triplet extraction to capture:
        - Rich concept definitions with metadata / 含元数据的概念定义
        - Semantic relationships with context / 带上下文的关系
        - Deep insights and implicit knowledge / 深层洞察和隐含知识

        The extraction is guided by:
        - Document-level context (themes, domains) / 文档级上下文
        - Optional user prompt focus / 可选的用户提示关注点

        Args:
            chunk:             Text chunk to analyze / 要分析的文本块
            document_context:  Document-level analysis from Stage 1
                              / 从第一阶段获取的文档级分析结果
            user_prompt:       Optional user-defined analysis focus
                             / 可选的自定义分析关注点

        Returns:
            Dict with keys:
            - concepts:  List of rich concept dicts / 丰富概念列表
            - triplets:  List of Triplet objects / 三元组对象列表
            - insights:  List of deep insight strings / 深度洞察字符串列表
        """
        themes = ", ".join(document_context.get("themes", []))
        domains = ", ".join(document_context.get("domains", []))

        base_system_prompt = (
            f"你是一个知识图谱构建专家。"
            f"当前文档主题：{themes}，涉及领域：{domains}。\n\n"
            "你的任务是深度分析文本，提取结构化知识，"
            "而不仅仅是格式转换。\n\n"
            "请提取：\n"
            "1. **核心概念**：识别重要的实体、术语、理论等\n"
            "2. **概念属性**：每个概念的定义、特征、分类等\n"
            "3. **概念关系**：概念之间的语义关系"
            "（因果、包含、对比等）\n"
            "4. **隐含知识**：文本暗示但未明说的知识\n\n"
            '返回JSON格式：\n'
            '{{\n'
            '    "concepts": [\n'
            '        {{\n'
            '            "name": "概念名称",\n'
            '            "description": "详细描述'
            '（用你的理解总结，不是照抄原文）",\n'
            '            "domain": "所属领域",\n'
            '            "category": "概念类型'
            '（如：理论/方法/工具/人物/事件等）",\n'
            '            "attributes": {{"属性名": "属性值"}},\n'
            '            "aliases": ["别名1", "别名2"],\n'
            '            "importance": "high/medium/low"\n'
            '        }}\n'
            '    ],\n'
            '    "triplets": [\n'
            '        {{\n'
            '            "subject": "主体概念",\n'
            '            "predicate": "关系类型'
            '（用语义化的动词，如：导致/包含/优于/依赖等）",\n'
            '            "object": "客体概念",\n'
            '            "context": "关系的上下文说明"\n'
            '        }}\n'
            '    ],\n'
            '    "insights": ["洞察1", "洞察2"]  '
            "// 你从文本中获得的深层理解\n"
            "}}"
        )

        # Incorporate user prompt / 融合用户提示词
        if user_prompt:
            system_prompt = (
                f"{base_system_prompt}\n\n"
                f"用户特别要求：{user_prompt}\n"
                f"请在分析时特别关注用户的需求。"
            )
        else:
            system_prompt = base_system_prompt

        try:
            response_text = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"请深度分析以下文本并提取知识：\n\n"
                            f"{chunk.text}"
                        ),
                    },
                ],
                temperature=0.5,  # Slightly higher for creative insights
                json_mode=True,
            )

            result = json.loads(response_text)

            # Convert to internal data structures / 转换为内部数据结构
            concepts = []
            for c in result.get("concepts", []):
                concepts.append({
                    "name": c.get("name", ""),
                    "description": c.get("description", ""),
                    "domain": c.get("domain", ""),
                    "category": c.get("category", ""),
                    "attributes": c.get("attributes", {}),
                    "aliases": c.get("aliases", []),
                    "importance": c.get("importance", "medium"),
                })

            triplets = []
            for t in result.get("triplets", []):
                triplets.append(
                    Triplet(
                        subject=t.get("subject", ""),
                        predicate=t.get("predicate", ""),
                        object=t.get("object", ""),
                        context=t.get("context", ""),
                    )
                )

            return {
                "concepts": concepts,
                "triplets": triplets,
                "insights": result.get("insights", []),
            }

        except Exception as e:
            print(f"⚠️  知识提取失败: {str(e)}")
            return {"concepts": [], "triplets": [], "insights": []}
