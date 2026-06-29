"""
Settings API Routes
===================

应用配置管理 API 路由，提供 AI 提供商和系统设置的动态配置。

API endpoints for managing application settings dynamically at runtime.
Supports reading current settings, updating AI provider configuration,
testing connections, and managing Redis connectivity.

Key features / 主要特性::

    - List supported AI providers / 列出所有支持的 AI 提供商
    - Get/set runtime settings / 读取和设置运行时配置
    - Test AI provider connectivity / 测试 AI 提供商连接
    - Check Redis health / 检查 Redis 健康状态
    - Discover available Ollama models / 发现可用的 Ollama 模型

Security / 安全性::
    API keys are masked (shown as "***") when reading settings back.
    读取配置时 API 密钥会被遮蔽显示为 "***"。
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from infra.config import settings
from infra.ai_providers import AIProviderFactory
from services.config_service import config_service

router = APIRouter(prefix="/settings", tags=["settings"])


class AISettings(BaseModel):
    """
    AI provider configuration request model.
    AI 提供商配置请求模型。

    Supports both the new universal API key format (ai_*) and
    the legacy provider-specific format (openai_*, ollama_*) for
    backward compatibility.

    Attributes:
        ai_provider:     AI provider identifier / AI 提供商标识
        ai_api_key:      Universal API key / 通用 API 密钥
        ai_model:        Model name override / 模型名称覆盖
        ai_base_url:     Custom API base URL / 自定义 API 地址
        openai_api_key:  Legacy OpenAI API key / 遗留 OpenAI API 密钥
        openai_model:    Legacy OpenAI model / 遗留 OpenAI 模型
        openai_base_url: Legacy OpenAI base URL / 遗留 OpenAI API 地址
        ollama_base_url: Ollama server URL / Ollama 服务地址
        ollama_model:    Ollama model name / Ollama 模型名称
    """
    ai_provider: Literal[
        "openai", "anthropic", "google", "deepseek", "qwen",
        "glm", "moonshot", "ernie", "minimax", "doubao",
        "ollama", "mock"
    ]
    # Universal config / 通用配置
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    # Legacy backward-compatible config / 向后兼容的旧配置
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"


class DatabaseSettings(BaseModel):
    """Database configuration (read-only from env)."""
    neo4j_uri: str
    neo4j_user: str
    redis_url: str


class AllSettings(BaseModel):
    """Combined application settings model."""
    ai_provider: Literal[
        "openai", "anthropic", "google", "deepseek", "qwen",
        "glm", "moonshot", "ernie", "minimax", "doubao",
        "ollama", "mock"
    ]
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    ai_base_url: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str
    openai_base_url: Optional[str] = None
    ollama_base_url: str
    ollama_model: str
    neo4j_uri: str
    neo4j_user: str
    redis_url: str


@router.get("/ai-providers")
async def list_ai_providers():
    """
    List all supported AI providers with their default configurations.
    列出所有支持的 AI 提供商及其默认配置。

    GET /settings/ai-providers

    Returns:
        Dict with providers list, each containing:
        - id: Provider identifier / 提供商标识
        - name: Display name / 显示名称
        - default_model: Default model name / 默认模型
        - requires_api_key: Whether API key is needed / 是否需要 API 密钥
    """
    return {"providers": AIProviderFactory.list_providers()}


@router.get("/")
async def get_settings():
    """
    Get current application settings.
    获取当前应用配置。

    GET /settings/

    Reads from Neo4j runtime config and falls back to environment variables.
    API keys are masked with "***" for security.

    Returns:
        Dict with all current settings (API keys masked)
        包含所有当前配置的字典（API 密钥已遮蔽）
    """
    runtime_config = config_service.get_runtime_config()

    return {
        "ai_provider": runtime_config.get("ai_provider"),
        "ai_api_key": (
            "***" if runtime_config.get("ai_api_key") else None
        ),
        "ai_model": runtime_config.get("ai_model"),
        "ai_base_url": runtime_config.get("ai_base_url"),
        "openai_api_key": (
            "***" if runtime_config.get("openai_api_key") else None
        ),
        "openai_model": runtime_config.get("openai_model"),
        "openai_base_url": runtime_config.get("openai_base_url"),
        "ollama_base_url": runtime_config.get("ollama_base_url"),
        "ollama_model": runtime_config.get("ollama_model"),
        # Infrastructure config from env (read-only)
        # 基础设施配置仍从环境变量读取（只读）
        "neo4j_uri": settings.neo4j_uri,
        "neo4j_user": settings.neo4j_user,
        "redis_url": settings.redis_url,
    }


@router.post("/ai")
async def update_ai_settings(ai_settings: AISettings):
    """
    Update AI provider settings (runtime, persists in Neo4j).
    更新 AI 提供商配置（运行时更新，持久化到 Neo4j）。

    POST /settings/ai

    Updates take effect immediately without application restart.
    New AI clients will use the updated configuration on creation.

    Args:
        ai_settings:  New AI configuration values / 新的 AI 配置值

    Returns:
        Dict with success status and message / 包含成功状态和消息的字典

    Raises:
        500: If Neo4j save fails / 如果 Neo4j 保存失败
    """
    try:
        # Prepare config update / 准备要更新的配置
        config_update = {
            "ai_provider": ai_settings.ai_provider,
        }

        # Update universal config / 更新通用配置
        if ai_settings.ai_api_key and ai_settings.ai_api_key != "***":
            config_update['ai_api_key'] = ai_settings.ai_api_key
        if ai_settings.ai_model:
            config_update['ai_model'] = ai_settings.ai_model
        else:
            config_update['ai_model'] = None
        if ai_settings.ai_base_url:
            config_update['ai_base_url'] = ai_settings.ai_base_url
        else:
            config_update['ai_base_url'] = None

        # Update legacy compatibility config / 更新兼容性配置
        if (
            ai_settings.openai_api_key
            and ai_settings.openai_api_key != "***"
        ):
            config_update[
                'openai_api_key'
            ] = ai_settings.openai_api_key
        config_update['openai_model'] = ai_settings.openai_model
        if ai_settings.openai_base_url:
            config_update[
                'openai_base_url'
            ] = ai_settings.openai_base_url
        else:
            config_update['openai_base_url'] = None

        config_update[
            'ollama_base_url'
        ] = ai_settings.ollama_base_url
        config_update['ollama_model'] = ai_settings.ollama_model

        # Save to Neo4j / 保存到数据库
        success = config_service.update_runtime_config(config_update)

        if success:
            return {
                "success": True,
                "message": "AI 配置已成功更新，立即生效",
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save configuration to database",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}",
        )


@router.post("/test-connection")
async def test_ai_connection(ai_settings: AISettings):
    """
    Test AI provider connectivity with the provided settings.
    使用提供的配置测试 AI 提供商连接。

    POST /settings/test-connection

    Creates a temporary AI client with the given settings and sends
    a simple "Hello" message to verify the connection works.

    Args:
        ai_settings:  AI configuration to test / 待测试的 AI 配置

    Returns:
        Dict with success status and connection message
        包含成功状态和连接消息的字典
    """
    try:
        if ai_settings.ai_provider == "mock":
            return {
                "success": True,
                "message": "Mock 模式 - 无需连接测试",
            }

        # Resolve API key and model with backward compatibility
        # 使用兼容性逻辑解析 API 密钥和模型
        api_key = ai_settings.ai_api_key
        model = ai_settings.ai_model
        base_url = ai_settings.ai_base_url

        if ai_settings.ai_provider == "openai" and not api_key:
            api_key = ai_settings.openai_api_key
            model = model or ai_settings.openai_model
            base_url = base_url or ai_settings.openai_base_url
        elif ai_settings.ai_provider == "ollama" and not base_url:
            base_url = ai_settings.ollama_base_url
            model = model or ai_settings.ollama_model

        # Filter out "***" placeholder / 过滤掉 "***" 占位符
        if api_key == "***":
            api_key = None

        client = AIProviderFactory.create_client(
            provider=ai_settings.ai_provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

        # Simple test call / 简单的测试调用
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.3,
            max_tokens=5,
        )

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
        }
        provider_name = provider_names.get(
            ai_settings.ai_provider, ai_settings.ai_provider
        )

        return {
            "success": True,
            "message": f"成功连接到 {provider_name} "
                       f"(模型: {client.model})",
        }

    except ValueError as e:
        return {
            "success": False,
            "message": f"配置错误: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
        }


@router.get("/redis/health")
async def redis_health():
    """
    Check Redis connection health.
    检查 Redis 连接健康状态。

    GET /settings/redis/health

    Returns detailed Redis server information including:
    - Connection status / 连接状态
    - Redis version / Redis 版本
    - Memory usage / 内存使用
    - Hit rate / 命中率
    - Namespace key count / 命名空间 key 数量

    Returns:
        Dict with health status, detailed data, and message
    """
    try:
        from infra.queue import get_queue

        queue = get_queue()
        health = queue.health_check()
        return {
            "success": health["connected"],
            "data": health,
            "message": (
                "Redis 连接正常"
                if health["connected"]
                else "Redis 未连接"
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "data": {"connected": False, "error": str(e)},
            "message": f"Redis 健康检查异常: {str(e)}",
        }


@router.get("/ollama/models")
async def get_ollama_models():
    """
    Get available Ollama models from the configured Ollama server.
    从已配置的 Ollama 服务器获取可用模型列表。

    GET /settings/ollama/models

    Returns:
        Dict with success status and list of model names
        包含成功状态和模型名称列表的字典
    """
    try:
        import httpx

        # Read Ollama URL from runtime config / 从运行时配置读取 Ollama 地址
        runtime_config = config_service.get_runtime_config()
        ollama_url = runtime_config.get(
            "ollama_base_url", settings.ollama_base_url
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [
                    model['name'] for model in data.get('models', [])
                ]
                return {"success": True, "models": models}
            else:
                return {
                    "success": False,
                    "message": "Failed to fetch Ollama models",
                }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to connect to Ollama: {str(e)}",
        }
