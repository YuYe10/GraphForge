"""
AI Provider Configuration and Unified Interface
=================================================

AI 服务提供商配置与统一接口模块，支持多种主流 LLM。

Provides a unified interface for interacting with multiple AI providers.
The system uses a factory pattern to create provider-specific clients while
presenting a consistent API for chat completion.

Supported providers / 支持的 AI 提供商::

    +------------+---------------------+----------------------------+
    | Provider   | Service             | Default Model              |
    +------------+---------------------+----------------------------+
    | openai     | OpenAI GPT          | gpt-4o-mini                |
    | anthropic  | Anthropic Claude    | claude-3-5-sonnet-20241022 |
    | google     | Google Gemini       | gemini-2.0-flash-exp       |
    | deepseek   | DeepSeek            | deepseek-chat              |
    | qwen       | 阿里云通义千问      | qwen-plus                  |
    | glm        | 智谱AI (GLM)        | glm-4-flash                |
    | moonshot   | 月之暗面 Kimi       | moonshot-v1-8k             |
    | ernie      | 百度文心一言        | ernie-4.0-8k-latest        |
    | minimax    | MiniMax             | abab6.5s-chat              |
    | doubao     | 字节豆包            | doubao-pro-4k              |
    | ollama     | Ollama (local)      | llama3                     |
    | mock       | Mock (testing)      | mock                       |
    +------------+---------------------+----------------------------+

Architecture / 架构说明::

    BaseAIClient  (abstract interface / 抽象接口)
        ├── OpenAIClient            (OpenAI native SDK)
        ├── AnthropicClient         (Anthropic native SDK)
        ├── GoogleGeminiClient      (OpenAI-compatible wrapper)
        ├── OpenAICompatibleClient  (DeepSeek, Qwen, GLM, etc.)
        ├── MockClient              (Testing without API calls)
        └── MockAIClient            (Legacy fallback)

    AIProviderFactory.create_client()  →  Returns appropriate client
"""
from typing import Optional, Literal, List, Dict, Any
from openai import OpenAI
import anthropic
import json


# Supported AI provider types / 支持的 AI 提供商类型
AIProviderType = Literal[
    "openai",           # OpenAI GPT
    "anthropic",        # Anthropic Claude
    "google",           # Google Gemini
    "deepseek",         # DeepSeek
    "qwen",             # 阿里云通义千问
    "glm",              # 智谱AI (GLM)
    "moonshot",         # 月之暗面 Kimi
    "ernie",            # 百度文心一言
    "minimax",          # MiniMax
    "doubao",           # 字节豆包
    "ollama",           # Ollama 本地模型
    "mock",             # Mock 模式（测试用）
]


class BaseAIClient:
    """
    Abstract base class for all AI clients.
    所有 AI 客户端的抽象基类。

    Defines the unified interface that all provider-specific clients must
    implement. The core method is chat_completion() which all downstream
    code uses regardless of the underlying provider.

    Attributes:
        model:   Model name / 模型名称
        kwargs:  Additional initialization parameters / 额外的初始化参数
    """

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.kwargs = kwargs

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Send a chat completion request to the AI provider.
        向 AI 提供商发送聊天补全请求。

        Args:
            messages:     List of message dicts with 'role' and 'content'
                         - role: "system" | "user" | "assistant"
                         - content: Message text
            temperature:  Sampling temperature (0.0 = deterministic, 1.0 = creative)
                         / 采样温度（0.0=确定性，1.0=创造性）
            extra_params: Additional provider-specific parameters, including:
                         - json_mode (bool): Request JSON-formatted response
                         - max_tokens (int): Maximum tokens in response

        Returns:
            Response text content as a string / 响应文本内容

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError


class OpenAIClient(BaseAIClient):
    """
    OpenAI GPT client using the official Python SDK.
    OpenAI GPT 客户端，使用官方 Python SDK。

    Supports all OpenAI-compatible endpoints and features, including
    JSON mode via the response_format parameter.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ):
        super().__init__(model)
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Send chat completion via OpenAI API.
        通过 OpenAI API 发送聊天补全请求。

        Handles json_mode by setting response_format to {"type": "json_object"}.
        The model must support JSON mode (gpt-4o-mini and later).

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Sampling temperature / 采样温度
            extra_params: Extra parameters (supports json_mode, max_tokens, etc.)

        Returns:
            Response text / 响应文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format=(
                {"type": "json_object"}
                if extra_params.get("json_mode")
                else None
            ),
            **{k: v for k, v in extra_params.items() if k != "json_mode"}
        )
        return response.choices[0].message.content


class AnthropicClient(BaseAIClient):
    """
    Anthropic Claude client using the official Python SDK.
    Anthropic Claude 客户端，使用官方 Python SDK。

    Handles the different message format that Anthropic uses:
    - System messages are extracted and passed separately
    - JSON mode instruction is injected into the system prompt
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ):
        super().__init__(model)
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = anthropic.Anthropic(**kwargs)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Send chat completion via Anthropic API.
        通过 Anthropic API 发送聊天补全请求。

        The Anthropic API separates system prompts from user/assistant messages.
        This method handles that conversion transparently.

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Sampling temperature / 采样温度
            extra_params: Extra parameters (supports json_mode, max_tokens)

        Returns:
            Response text / 响应文本
        """
        # Anthropic separates system messages / Anthropic 将 system 消息分离
        system_msg = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        # Inject JSON mode instruction into system prompt
        # 在 system prompt 中注入 JSON 模式要求
        if extra_params.get("json_mode"):
            json_instruction = (
                "\n\n重要：请确保返回的内容是有效的 JSON 格式，"
                "不要包含任何额外的文本或说明。"
            )
            if system_msg:
                system_msg = system_msg + json_instruction
            else:
                system_msg = json_instruction.strip()

        kwargs = {
            "model": self.model,
            "messages": user_messages,
            "temperature": temperature,
            "max_tokens": extra_params.get("max_tokens", 4096),
        }

        # Remove json_mode from params (not a valid Anthropic parameter)
        kwargs = {k: v for k, v in kwargs.items() if k != "json_mode"}

        if system_msg:
            kwargs["system"] = system_msg

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class GoogleGeminiClient(BaseAIClient):
    """
    Google Gemini client via OpenAI-compatible proxy.
    Google Gemini 客户端，通过 OpenAI 兼容接口访问。

    Google provides an OpenAI-compatible API endpoint, so we can reuse
    the OpenAI client with a different base_url.
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None
    ):
        super().__init__(model)
        self.client = OpenAI(
            api_key=api_key,
            base_url=(
                base_url
                or "https://generativelanguage.googleapis.com/v1beta/openai/"
            ),
        )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Send chat completion via Google Gemini API (OpenAI-compatible).
        通过 Google Gemini API（OpenAI 兼容接口）发送请求。

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Sampling temperature / 采样温度
            extra_params: Extra parameters (supports json_mode)

        Returns:
            Response text / 响应文本
        """
        params = {k: v for k, v in extra_params.items() if k != "json_mode"}
        if extra_params.get("json_mode"):
            params["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            **params,
        )
        return response.choices[0].message.content


class OpenAICompatibleClient(BaseAIClient):
    """
    Generic OpenAI-compatible client for providers with compatible APIs.
    OpenAI 兼容接口的通用客户端。

    Supports providers that implement the OpenAI-compatible API format:
    DeepSeek, Qwen (通义千问), GLM (智谱AI), Moonshot/Kimi,
    ERNIE (文心一言), MiniMax, Doubao (豆包), and Ollama.

    Features auto-detection of Ollama URLs and automatic /v1 suffix addition.
    自动检测 Ollama URL 并添加 /v1 后缀。
    """

    def __init__(
        self, api_key: str, model: str, base_url: str
    ):
        super().__init__(model)
        # Normalize base_url: remove trailing slash (except Google's special case)
        # 规范化 base_url：移除末尾斜杠（除非是 Google 的特殊情况）
        normalized_base_url = (
            base_url.rstrip('/')
            if not base_url.endswith('/openai/')
            else base_url
        )

        # Special handling: Ollama needs /v1 suffix
        # 特殊处理：Ollama 需要 /v1 后缀
        if (
            ':11434' in normalized_base_url
            and not normalized_base_url.endswith('/v1')
        ):
            normalized_base_url = normalized_base_url + '/v1'
            print(
                "⚠️  [AI客户端] 检测到 Ollama base_url，"
                "已自动添加 /v1 后缀"
            )

        # Validate base_url format / 验证 base_url 格式
        if not normalized_base_url.startswith(('http://', 'https://')):
            raise ValueError(
                f"Invalid base_url format: {base_url}. "
                f"Must start with http:// or https://"
            )

        print(f"🔗 [AI客户端] 初始化 OpenAI 兼容客户端")
        print(f"   Model: {model}")
        print(f"   Base URL: {normalized_base_url}")

        self.client = OpenAI(
            api_key=api_key,
            base_url=normalized_base_url,
        )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Send chat completion via OpenAI-compatible API.
        通过 OpenAI 兼容 API 发送聊天补全请求。

        Provides detailed error messages for common issues like 404 errors
        (which often indicate an incorrect base_url configuration).

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Sampling temperature / 采样温度
            extra_params: Extra parameters (supports json_mode, max_tokens)

        Returns:
            Response text / 响应文本

        Raises:
            ValueError: If API endpoint returns 404 (configuration issue)
        """
        params = {k: v for k, v in extra_params.items() if k != "json_mode"}
        if extra_params.get("json_mode"):
            params["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                **params,
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            actual_base_url = getattr(self.client, 'base_url', 'unknown')

            if (
                "404" in error_msg
                or "not found" in error_msg.lower()
                or error_type == "NotFoundError"
            ):
                raise ValueError(
                    f"API endpoint not found (404). "
                    f"Please check your base_url configuration. "
                    f"Current base_url: {actual_base_url}, "
                    f"Model: {self.model}. "
                    f"This usually means:\n"
                    f"  1. The base_url is incorrect or incomplete\n"
                    f"  2. The API endpoint path is wrong\n"
                    f"  3. The service is not available at the specified URL\n"
                    f"Original error: {error_msg}"
                ) from e
            raise


class MockClient(BaseAIClient):
    """
    Mock client for testing without real API calls.
    用于测试的模拟客户端，无需真实 API 调用。

    Detects the type of request by analyzing the user message content and
    returns appropriate mock responses for:
    - Coreference resolution requests / 指代消解请求
    - General entity extraction / 通用实体抽取

    This allows development and testing without any AI provider configured.
    """

    def __init__(self):
        super().__init__("mock")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Return mock responses based on request type detection.
        根据请求类型检测返回模拟响应。

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Ignored in mock mode / 模拟模式下忽略
            extra_params: Ignored in mock mode / 模拟模式下忽略

        Returns:
            JSON-formatted mock response string / JSON 格式的模拟响应字符串
        """
        # Detect request type from user message / 从用户消息中检测请求类型
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break

        # Coreference resolution request / 指代消解请求
        if "指代消解" in user_message or "mention" in user_message.lower():
            import re
            resolutions = []
            mention_matches = re.findall(
                r'"mention_text":\s*"([^"]+)"', user_message
            )
            candidate_matches = re.findall(
                r'"text":\s*"([^"]+)"', user_message
            )

            if mention_matches and candidate_matches:
                for i, mention_text in enumerate(mention_matches[:3]):
                    if i < len(candidate_matches):
                        resolutions.append({
                            "mention_id": i + 1,
                            "mention_text": mention_text,
                            "antecedent_text": candidate_matches[0],
                            "confidence": 0.8,
                            "rationale": "Mock 模式：自动映射",
                        })

            if not resolutions:
                resolutions = [{
                    "mention_id": 1,
                    "mention_text": "它",
                    "antecedent_text": "示例实体",
                    "confidence": 0.7,
                    "rationale": "Mock 模式：默认响应",
                }]

            return json.dumps(
                {"resolutions": resolutions, "resolved_text": None},
                ensure_ascii=False,
            )

        # Default: entity extraction format / 默认：实体抽取格式
        return json.dumps(
            {
                "triplets": [
                    {
                        "subject": "示例主体",
                        "predicate": "relates_to",
                        "object": "示例客体",
                        "confidence": 0.5,
                        "language": "zh",
                    }
                ]
            },
            ensure_ascii=False,
        )


class AIProviderFactory:
    """
    Factory for creating AI clients based on provider type.
    AI 客户端工厂，根据提供商类型创建对应的客户端。

    Manages default base URLs and model names for all supported providers.
    Provides both client creation and provider information methods.

    Usage / 用法示例::

        client = AIProviderFactory.create_client(
            provider="qwen",
            api_key="sk-xxx",
            model="qwen-plus",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        response = client.chat_completion(messages=[...])
    """

    # Default base URLs for each provider
    # Note: base_url should NOT end with trailing slash (except Google)
    # 注意：base_url 不应以斜杠结尾（除了 Google 的特殊情况）
    DEFAULT_BASE_URLS = {
        "openai": None,  # Uses OpenAI default / 使用 OpenAI 默认
        "anthropic": None,
        "google": (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        ),
        "deepseek": "https://api.deepseek.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "glm": "https://open.bigmodel.cn/api/paas/v4",
        "moonshot": "https://api.moonshot.cn/v1",
        "ernie": (
            "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop"
        ),
        "minimax": "https://api.minimax.chat/v1",
        "doubao": "https://ark.cn-beijing.volces.com/api/v3",
        "ollama": "http://localhost:11434/v1",
    }

    # Default model names for each provider / 默认模型名称
    DEFAULT_MODELS = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "google": "gemini-2.0-flash-exp",
        "deepseek": "deepseek-chat",
        "qwen": "qwen-plus",
        "glm": "glm-4-flash",
        "moonshot": "moonshot-v1-8k",
        "ernie": "ernie-4.0-8k-latest",
        "minimax": "abab6.5s-chat",
        "doubao": "doubao-pro-4k",
        "ollama": "llama3",
        "mock": "mock",
    }

    @classmethod
    def create_client(
        cls,
        provider: AIProviderType,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> BaseAIClient:
        """
        Create an AI client based on provider type.
        根据提供商类型创建 AI 客户端。

        Args:
            provider:  AI provider identifier / AI 提供商标识
            api_key:   API key (not needed for mock/ollama) / API 密钥
            model:     Model name (uses default if not provided) / 模型名称
            base_url:  Custom base URL (uses default if not provided)
                      / 自定义 API 地址

        Returns:
            AI client instance / AI 客户端实例

        Raises:
            ValueError: If provider is not supported or missing required config
                        如果提供商不受支持或缺少必要配置
        """
        model = model or cls.DEFAULT_MODELS.get(provider)
        base_url = base_url or cls.DEFAULT_BASE_URLS.get(provider)

        if provider == "mock":
            return MockClient()

        if provider == "openai":
            if not api_key:
                raise ValueError("OpenAI API key is required")
            return OpenAIClient(api_key, model, base_url)

        if provider == "anthropic":
            if not api_key:
                raise ValueError("Anthropic API key is required")
            return AnthropicClient(api_key, model, base_url)

        if provider == "google":
            if not api_key:
                raise ValueError("Google API key is required")
            return GoogleGeminiClient(api_key, model, base_url)

        # OpenAI-compatible providers / OpenAI 兼容的提供商
        if provider in [
            "deepseek", "qwen", "glm", "moonshot",
            "ernie", "minimax", "doubao", "ollama",
        ]:
            if provider == "ollama":
                api_key = api_key or "ollama"  # Ollama doesn't need real key
            elif not api_key:
                raise ValueError(f"{provider} API key is required")

            return OpenAICompatibleClient(api_key, model, base_url)

        raise ValueError(f"Unsupported AI provider: {provider}")

    @classmethod
    def get_provider_info(cls, provider: AIProviderType) -> Dict[str, Any]:
        """
        Get provider information including default model and base URL.
        获取提供商信息，包括默认模型和默认 API 地址。

        Args:
            provider:  AI provider identifier / AI 提供商标识

        Returns:
            Dict with provider, default_model, default_base_url
            包含提供商、默认模型和默认 API 地址的字典
        """
        return {
            "provider": provider,
            "default_model": cls.DEFAULT_MODELS.get(provider),
            "default_base_url": cls.DEFAULT_BASE_URLS.get(provider),
        }

    @classmethod
    def list_providers(cls) -> List[Dict[str, Any]]:
        """
        List all supported providers with their configurations.
        列出所有支持的提供商及其配置。

        Returns:
            List of provider info dicts with id, name, default_model,
            and requires_api_key flag
            提供商信息字典列表
        """
        return [
            {
                "id": "openai",
                "name": "OpenAI GPT",
                "default_model": cls.DEFAULT_MODELS["openai"],
                "requires_api_key": True,
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "default_model": cls.DEFAULT_MODELS["anthropic"],
                "requires_api_key": True,
            },
            {
                "id": "google",
                "name": "Google Gemini",
                "default_model": cls.DEFAULT_MODELS["google"],
                "requires_api_key": True,
            },
            {
                "id": "deepseek",
                "name": "DeepSeek",
                "default_model": cls.DEFAULT_MODELS["deepseek"],
                "requires_api_key": True,
            },
            {
                "id": "qwen",
                "name": "阿里云通义千问",
                "default_model": cls.DEFAULT_MODELS["qwen"],
                "requires_api_key": True,
            },
            {
                "id": "glm",
                "name": "智谱AI (GLM)",
                "default_model": cls.DEFAULT_MODELS["glm"],
                "requires_api_key": True,
            },
            {
                "id": "moonshot",
                "name": "月之暗面 Kimi",
                "default_model": cls.DEFAULT_MODELS["moonshot"],
                "requires_api_key": True,
            },
            {
                "id": "ernie",
                "name": "百度文心一言",
                "default_model": cls.DEFAULT_MODELS["ernie"],
                "requires_api_key": True,
            },
            {
                "id": "minimax",
                "name": "MiniMax",
                "default_model": cls.DEFAULT_MODELS["minimax"],
                "requires_api_key": True,
            },
            {
                "id": "doubao",
                "name": "字节豆包",
                "default_model": cls.DEFAULT_MODELS["doubao"],
                "requires_api_key": True,
            },
            {
                "id": "ollama",
                "name": "Ollama",
                "default_model": cls.DEFAULT_MODELS["ollama"],
                "requires_api_key": False,
            },
            {
                "id": "mock",
                "name": "Mock (测试模式)",
                "default_model": "mock",
                "requires_api_key": False,
            },
        ]


# ══════════════════════════════════════════════════════════════════
# Legacy factory function (backward compatibility)
# 遗留工厂函数（向后兼容）
# ══════════════════════════════════════════════════════════════════


def get_ai_client(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Optional[BaseAIClient]:
    """
    Factory function to get AI client based on provider (legacy API).
    根据提供商获取 AI 客户端的工厂函数（遗留 API）。

    This function wraps AIProviderFactory for backward compatibility
    with older code that directly calls get_ai_client().

    Args:
        provider:  AI provider name / AI 提供商名称
        api_key:   API key / API 密钥
        model:     Model name (uses default if not specified) / 模型名称
        base_url:  Custom API base URL (optional) / 自定义 API 地址

    Returns:
        AI client instance or None if mock mode / AI 客户端实例

    Raises:
        ValueError: If provider is not supported / 如果提供商不受支持
    """
    # Default models for each provider / 各提供商的默认模型
    default_models = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-sonnet-20240229",
        "google": "gemini-1.5-pro",
        "qwen": "qwen-max",
        "glm": "glm-4",
        "deepseek": "deepseek-chat",
        "moonshot": "moonshot-v1-auto",
        "ernie": "ernie-4.0-turbo-latest",
        "minimax": "abab6.5s-chat",
        "doubao": "doubao-pro-32k",
        "ollama": "llama2",
        "mock": "mock",
    }

    if not model:
        model = default_models.get(provider, "default")

    if provider == "openai":
        if not api_key:
            raise ValueError("OpenAI requires api_key")
        return OpenAIClient(api_key=api_key, model=model, base_url=base_url)

    elif provider == "anthropic":
        if not api_key:
            raise ValueError("Anthropic Claude requires api_key")
        return AnthropicClient(
            api_key=api_key, model=model, base_url=base_url
        )

    elif provider == "google":
        if not api_key:
            raise ValueError("Google Gemini requires api_key")
        return GoogleGeminiClient(
            api_key=api_key, model=model, base_url=base_url
        )

    elif provider in [
        "qwen", "glm", "deepseek", "moonshot",
        "ernie", "minimax", "doubao", "ollama",
    ]:
        if provider != "ollama" and not api_key:
            raise ValueError(f"{provider} requires api_key")
        if not base_url:
            base_urls = {
                "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "glm": "https://open.bigmodel.cn/api/paas/v4",
                "deepseek": "https://api.deepseek.com",
                "moonshot": "https://api.moonshot.cn/v1",
                "ernie": (
                    "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/"
                    "wenxinworkshop/chat"
                ),
                "minimax": "https://api.minimaxi.chat/v1",
                "doubao": "https://ark.cn-beijing.volces.com/api/v3",
                "ollama": "http://localhost:11434/v1",
            }
            base_url = base_urls.get(provider)
        return OpenAICompatibleClient(
            api_key=api_key or "dummy", model=model, base_url=base_url
        )

    elif provider == "mock":
        return MockAIClient(model=model)

    else:
        raise ValueError(f"Unsupported provider: {provider}")


class MockAIClient(BaseAIClient):
    """
    Legacy mock AI client for testing (QA service).
    用于测试的遗留模拟 AI 客户端（QA 服务）。

    Provides simple text-based mock responses for common question types.
    Unlike MockClient, this returns human-readable text rather than JSON.
    """

    def __init__(self, model: str = "mock"):
        super().__init__(model)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        **extra_params
    ) -> str:
        """
        Return mock text responses based on question content.
        根据问题内容返回模拟文本响应。

        Supports predefined responses for:
        - Knowledge graph questions / 知识图谱相关问题
        - AI-related questions / AI 相关问题
        - Generic fallback / 通用回退

        Args:
            messages:     Chat messages / 聊天消息
            temperature:  Ignored in mock mode / 模拟模式下忽略
            extra_params: Ignored in mock mode

        Returns:
            Mock response text / 模拟响应文本
        """
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")

        if "知识图谱" in user_message or "graph" in user_message.lower():
            return (
                "知识图谱是一种以图形结构表示知识的方法，"
                "它通过节点（实体）和边（关系）来组织和展示知识。\n\n"
                "**主要特点：**\n"
                "- **节点**：代表实体（人物、地点、概念等）\n"
                "- **边**：表示实体之间的关系\n"
                "- **应用**：搜索、推荐系统、自然语言处理\n\n"
                "知识图谱广泛应用于Google搜索、维基百科等大型应用中。"
            )

        elif "人工智能" in user_message or "AI" in user_message:
            return (
                "人工智能（AI）是计算机科学的一个分支，"
                "旨在创建能够执行通常需要人类智能的任务的机器。\n\n"
                "**主要领域：**\n"
                "- 机器学习\n"
                "- 深度学习\n"
                "- 自然语言处理\n"
                "- 计算机视觉\n\n"
                "人工智能已经成为现代社会的重要技术。"
            )

        else:
            return (
                f"这是一个Mock模式的测试回答。\n\n"
                f"您的问题是: {user_message[:100]}\n\n"
                f"在实际应用中，这里会返回由AI模型生成的真实答案，"
                f"同时配合知识图谱中的相关信息。"
            )
