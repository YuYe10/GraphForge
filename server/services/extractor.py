"""
Triplet Extraction Service using LLM
=====================================

三元组提取服务，利用大语言模型从文本中抽取结构化知识。

Extracts subject-predicate-object triplets from text chunks using an LLM.
Supports multiple AI providers through the unified AIProviderFactory interface.
Falls back to mock mode when no AI provider is configured.

Extraction pipeline / 提取流水线::

    Text Chunk
        │
        ▼
    _build_prompt()  →  Bilingual prompt with relationship type guide
        │
        ▼
    AIProvider.chat_completion()  →  JSON response
        │
        ▼
    JSON parsing + validation  →  List[Triplet]
        │
        ▼
    Entity linker  →  Linked triplets
"""
from typing import List, Optional
from infra.ai_providers import AIProviderFactory, BaseAIClient
from models.document import Triplet, Chunk
from services.config_service import config_service


class TripletExtractor:
    """
    Extract knowledge triplets from text using LLM.
    使用 LLM 从文本中提取知识三元组。

    Handles AI provider initialization, prompt construction, API communication,
    response parsing, and graceful fallback to mock mode.

    The extraction prompt supports both Chinese and English text, with a
    comprehensive relationship type guide covering 14+ semantic relations.

    Attributes:
        client:    AI client instance / AI 客户端实例
        provider:  AI provider name / AI 提供商名称
        model:     Model name / 模型名称
    """

    def __init__(self):
        self.client: Optional[BaseAIClient] = None
        self.provider = None
        self.model = None

        try:
            # Load AI configuration from runtime config (Neo4j database)
            # 从数据库读取运行时配置
            ai_config = config_service.get_ai_provider_config()
            self.provider = ai_config["provider"]
            api_key = ai_config["api_key"]
            model = ai_config["model"]
            base_url = ai_config["base_url"]

            # Mock mode doesn't need a real API key
            if self.provider == "mock":
                api_key = api_key or "mock"

            # Create AI client / 创建AI客户端
            self.client = AIProviderFactory.create_client(
                provider=self.provider,
                api_key=api_key,
                model=model,
                base_url=base_url,
            )
            self.model = self.client.model

            # Display provider info / 显示提供商信息
            provider_names = {
                "openai": "OpenAI GPT",
                "anthropic": "Anthropic Claude",
                "google": "Google Gemini",
                "deepseek": "DeepSeek",
                "qwen": "阿里云通义千问",
                "glm": "智谱AI (GLM)",
                "moonshot": "月之暗面 Kimi",
                "ernie": "百度文心一言",
                "minimax": "MiniMax",
                "doubao": "字节豆包",
                "ollama": "Ollama",
                "mock": "Mock",
            }
            provider_name = provider_names.get(self.provider, self.provider)

            if self.provider != "mock":
                print(f"✅ 使用 {provider_name}，模型: {self.model}")
            else:
                print("ℹ️  使用 Mock 模式进行三元组提取")

        except ValueError as e:
            print(f"⚠️  警告: AI 配置错误 ({e})，将使用 mock 模式")
            self.provider = "mock"
            self.client = AIProviderFactory.create_client("mock")
            self.model = "mock"
        except Exception as e:
            print(
                f"⚠️  警告: 无法初始化 AI 客户端 ({e})，"
                f"将使用 mock 模式"
            )
            self.provider = "mock"
            self.client = AIProviderFactory.create_client("mock")
            self.model = "mock"

    def extract(self, chunk: Chunk) -> List[Triplet]:
        """
        Extract triplets from a text chunk using AI.
        使用 AI 从文本块中提取三元组。

        Process flow / 处理流程::

            1. Build bilingual extraction prompt / 构建双语提取提示词
            2. Send to AI provider with json_mode / 发送给 AI 提供商
            3. Parse JSON response / 解析 JSON 响应
            4. Filter invalid triplets (missing required fields)
               / 过滤无效三元组
            5. Return validated Triplet objects / 返回验证后的三元组列表

        Args:
            chunk:  Text chunk to extract from / 要提取的文本块

        Returns:
            List of validated Triplet objects / 验证后的三元组列表
            Empty list on failure / 失败时返回空列表
        """
        print(f"\n{'='*80}")
        print(
            f"🔍 [知识抽取] 开始处理文本块 "
            f"(chunk_id: {chunk.chunk_id})"
        )
        print(f"📄 文本长度: {len(chunk.text)} 字符")
        print(f"📝 文本预览: {chunk.text[:200]}...")

        if not self.client or self.provider == "mock":
            print(
                f"⚠️  [知识抽取] 使用 Mock 模式"
                f"（未配置 AI 服务）"
            )
            result = self._mock_extract(chunk)
            print(
                f"📊 [知识抽取] Mock 模式提取结果: "
                f"{len(result)} 个三元组"
            )
            return result

        prompt = self._build_prompt(chunk.text)
        raw_content = None

        try:
            print(
                f"🤖 [AI请求] Provider: {self.provider}, "
                f"Model: {self.model}"
            )
            print(f"📤 [AI请求] 发送请求到 AI 服务...")

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a knowledge extraction expert. "
                        "Extract subject-predicate-object triplets "
                        "from the given text. "
                        "Return only valid JSON array."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            # Send to AI with JSON mode / 使用 json_mode 发送
            raw_content = self.client.chat_completion(
                messages=messages,
                temperature=0.3,
                json_mode=True,
            )
            print(
                f"📥 [AI响应] 收到响应，长度: "
                f"{len(raw_content)} 字符"
            )
            print(
                f"📥 [AI响应] 原始内容预览: "
                f"{raw_content[:500]}..."
            )

            # Parse JSON response / 解析 JSON 响应
            import json

            result = json.loads(raw_content)
            raw_triplets = result.get("triplets", [])
            print(
                f"📊 [AI响应] 解析到原始三元组数量: "
                f"{len(raw_triplets)}"
            )

            # Display first few triplets / 显示前几个三元组
            for idx, t in enumerate(raw_triplets[:5], 1):
                print(
                    f"   [{idx}] "
                    f"{t.get('subject', 'N/A')} - "
                    f"{t.get('predicate', 'N/A')} - "
                    f"{t.get('object', 'N/A')} "
                    f"(置信度: {t.get('confidence', 0)})"
                )
            if len(raw_triplets) > 5:
                print(
                    f"   ... 还有 {len(raw_triplets) - 5} 个三元组"
                )

            # Convert to Triplet objects, filtering invalid ones
            # 转换为 Triplet 对象，过滤无效三元组
            triplets = [
                Triplet(
                    subject=t.get("subject", ""),
                    predicate=t.get("predicate", ""),
                    object=t.get("object", ""),
                    confidence=t.get("confidence", 0.8),
                    evidence={
                        "docId": chunk.doc_id,
                        "chunkId": chunk.chunk_id,
                        "page": chunk.meta.get("page"),
                        "offset": chunk.meta.get("offset"),
                        "text": chunk.text[:200],
                    },
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                )
                for t in raw_triplets
                if t.get("subject")
                and t.get("predicate")
                and t.get("object")
            ]

            filtered_count = len(raw_triplets) - len(triplets)
            if filtered_count > 0:
                print(
                    f"⚠️  [过滤] 过滤掉 {filtered_count} 个"
                    f"无效三元组（缺少必要字段）"
                )

            print(
                f"✅ [知识抽取] 成功提取 {len(triplets)} 个有效三元组"
            )
            print(f"{'='*80}\n")

            return triplets

        except json.JSONDecodeError as e:
            print(f"❌ [知识抽取] JSON 解析错误: {e}")
            if raw_content:
                print(
                    f"📥 [AI响应] 原始响应内容: "
                    f"{raw_content[:1000]}"
                )
            return []
        except Exception as e:
            print(f"❌ [知识抽取] 提取失败: {e}")
            import traceback

            print(f"📋 [错误详情] {traceback.format_exc()}")
            return []

    def _build_prompt(self, text: str) -> str:
        """
        Build a bilingual extraction prompt for both Chinese and English text.
        构建支持中英文的双语提取提示词。

        The prompt includes:
        - Task description in both languages
        - 14 relationship types with bilingual descriptions
        - Strict JSON output format specification
        - Quality guidelines (confidence, language preservation)

        Args:
            text:  The text content to extract from / 待提取的文本内容

        Returns:
            Formatted prompt string / 格式化后的提示词字符串
        """
        return f"""You are a professional knowledge graph construction expert. Extract structured knowledge triplets (subject-relation-object) from the given text.
你是一个专业的知识图谱构建专家。请从以下文本中提取结构化的知识三元组（主体-关系-客体）。

**Text Content / 文本内容：**
{text}

**Task Requirements / 任务要求：**
1. Identify core concepts, entities, and key information / 识别核心概念、实体和关键信息
2. Extract semantic relationships between them / 提取它们之间的语义关系
3. Perform structured organization and optimization / 进行结构化整理和优化
4. Ensure knowledge practicality and accuracy / 确保知识具有实用性和准确性
5. **Preserve original language**: Keep concepts in their original language (Chinese/English) / **保留原始语言**：保持概念的原始语言（中英文）

**Relationship Types Guide / 关系类型指南：**
- `is_a` / `定义为`: A is a type/kind of B / A 是 B 的一种/一类
- `contains` / `包含`: A contains B as a component / A 包含 B 作为组成部分
- `belongs_to` / `属于`: A belongs to category B / A 属于 B 类别
- `has_property` / `具有属性`: A has characteristic or attribute / A 具有某种特性或属性
- `used_for` / `用于`: A is used to achieve/accomplish B / A 用于实现/完成 B
- `affects` / `影响`: A affects B / A 对 B 产生影响
- `relates_to` / `关联`: A is related to B / A 与 B 存在关联
- `composed_of` / `由...组成`: A is composed of B / A 由 B 组成
- `produces` / `产生`: A produces/generates B / A 产生/生成 B
- `depends_on` / `依赖`: A depends on B / A 依赖于 B
- `causes` / `导致`: A causes B / A 导致 B
- `implements` / `实现`: A implements B / A 实现了 B
- `derived_from` / `派生自`: A is derived from B / A 派生自 B
- `similar_to` / `相似于`: A is similar to B / A 与 B 相似

**Output Format (Pure JSON) / 输出格式（纯 JSON）：**
{{
  "triplets": [
    {{
      "subject": "Concept/Entity Name",
      "predicate": "Relationship Type (use types from guide above)",
      "object": "Target Concept/Entity/Attribute Value",
      "confidence": 0.85,
      "language": "en" or "zh" or "mixed"
    }}
  ]
}}

**Important Notes / 注意事项：**
- Subject and object should be concise, standardized nouns or noun phrases / 主体和客体应该是简洁、规范的名词或名词短语
- Keep the original language of concepts (do NOT translate) / 保持概念的原始语言（不要翻译）
- Use English relationship type identifiers (e.g., "is_a", "contains") / 使用英文关系类型标识符
- Confidence should reflect knowledge certainty (0.0-1.0) / confidence 应反映知识确定程度（0.0-1.0）
- Give higher confidence to definitional, structural knowledge / 对定义性、结构性知识给予更高置信度
- Ignore trivial details, focus on core knowledge / 忽略无关细节，聚焦核心知识点
- If no clear knowledge in text, return empty array / 如果文本中没有明确知识点，返回空数组

Return ONLY the JSON object, no other explanatory text.
只返回 JSON 对象，不要包含任何其他文字说明。"""

    def _mock_extract(self, chunk: Chunk) -> List[Triplet]:
        """
        Mock extraction using simple rule-based patterns.
        使用简单规则模式进行模拟提取（无需 AI API）。

        Extracts "X is Y" patterns from English text as a demonstration.
        This allows the extraction pipeline to function without an AI provider.

        Args:
            chunk:  Text chunk to extract from / 待提取的文本块

        Returns:
            List of Triplet objects from regex matching / 正则匹配的三元组列表
        """
        import re

        triplets = []
        text = chunk.text

        # Look for "X is a Y" patterns / 查找"X is a Y"模式
        is_pattern = re.compile(
            r'([A-Z][a-zA-Z\s]+?)\s+is\s+(?:a\s+)?'
            r'([a-zA-Z\s]+?)(?:\.|,|$)'
        )
        for match in is_pattern.finditer(text):
            triplets.append(
                Triplet(
                    subject=match.group(1).strip(),
                    predicate="is_a",
                    object=match.group(2).strip(),
                    confidence=0.7,
                    evidence={
                        "docId": chunk.doc_id,
                        "chunkId": chunk.chunk_id,
                        "page": chunk.meta.get("page"),
                        "offset": chunk.meta.get("offset"),
                        "text": chunk.text[:200],
                    },
                    doc_id=chunk.doc_id,
                    chunk_id=chunk.chunk_id,
                )
            )

        return triplets
