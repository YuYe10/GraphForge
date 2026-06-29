"""
Runtime Configuration Service (Neo4j-backed)
=============================================

运行时配置服务，使用 Neo4j 图数据库存储和管理应用配置。

Provides runtime configuration management that persists to Neo4j. This
allows configuration changes to take effect immediately without restarting
the application, and supports multiple configuration sources with priority:

Configuration priority / 配置优先级::

    1. Neo4j runtime config (user-set via API, highest priority)
    2. Environment variables (.env file, fallback)
    3. Pydantic defaults (lowest priority)

Architecture / 架构说明::

    ConfigService  (singleton: config_service)
        │
        ├── get_runtime_config()    → Read from Neo4j RuntimeConfig node
        ├── update_runtime_config() → Write to Neo4j RuntimeConfig node
        └── get_ai_provider_config() → Get current AI provider settings
                │
                └── Handles backward compatibility between
                    old (openai_*) and new (ai_*) config keys
"""
from typing import Optional, Dict, Any
from infra.neo4j_client import neo4j_client
from infra.config import settings as base_settings


class ConfigService:
    """
    Service for managing runtime configuration in Neo4j.
    Neo4j 运行时配置管理服务。

    Configuration is stored as a single RuntimeConfig node in Neo4j with
    all key-value pairs as node properties. This allows the application
    to dynamically change configuration without restart.

    The service gracefully handles cases where Neo4j is unavailable by
    falling back to environment-variable-based configuration.

    Attributes:
        CONFIG_NODE_ID:  Fixed ID for the single RuntimeConfig node
                        / 运行时配置节点的固定 ID
    """

    CONFIG_NODE_ID = "system_config"

    def get_runtime_config(self) -> Dict[str, Any]:
        """
        Get runtime configuration from Neo4j.
        从 Neo4j 获取运行时配置。

        Retrieves the RuntimeConfig node and extracts all configuration
        values. Falls back to environment variables if:
        - Neo4j is not initialized / Neo4j 未初始化
        - The RuntimeConfig node doesn't exist yet / 节点不存在
        - A query error occurs / 查询出错

        Returns:
            Dict with all configuration values / 包含所有配置值的字典
        """
        # If Neo4j is not initialized, return env config directly
        # 如果 Neo4j 未初始化，直接返回环境变量配置
        if not neo4j_client._initialized:
            return self._get_env_config()

        try:
            query = """
            MATCH (config:RuntimeConfig {id: $config_id})
            RETURN config
            """
            result = neo4j_client.execute_query(
                query, {"config_id": self.CONFIG_NODE_ID}
            )

            if result and result[0].get("config"):
                config_node = result[0]["config"]
                return {
                    "ai_provider": config_node.get(
                        "ai_provider", base_settings.ai_provider
                    ),
                    "ai_api_key": config_node.get("ai_api_key"),
                    "ai_model": config_node.get("ai_model"),
                    "ai_base_url": config_node.get("ai_base_url"),
                    # Legacy compatibility fields / 兼容性字段
                    "openai_api_key": config_node.get("openai_api_key"),
                    "openai_model": config_node.get(
                        "openai_model", base_settings.openai_model
                    ),
                    "openai_base_url": config_node.get("openai_base_url"),
                    "ollama_base_url": config_node.get(
                        "ollama_base_url",
                        base_settings.ollama_base_url,
                    ),
                    "ollama_model": config_node.get(
                        "ollama_model", base_settings.ollama_model
                    ),
                }
            else:
                # First run — initialize from environment variables
                # 首次运行——从环境变量初始化
                return self._initialize_from_env()
        except RuntimeError:
            # Neo4j not available — fall back to env config
            # Neo4j 不可用 — 回退到环境变量配置
            return self._get_env_config()

    def _get_env_config(self) -> Dict[str, Any]:
        """
        Get configuration from environment variables only (no DB).
        仅从环境变量获取配置（不访问数据库）。

        Returns:
            Dict with all configuration values from base_settings
            包含所有配置值的字典
        """
        return {
            "ai_provider": base_settings.ai_provider,
            "ai_api_key": base_settings.ai_api_key,
            "ai_model": base_settings.ai_model,
            "ai_base_url": base_settings.ai_base_url,
            "openai_api_key": base_settings.openai_api_key,
            "openai_model": base_settings.openai_model,
            "openai_base_url": base_settings.openai_base_url,
            "ollama_base_url": base_settings.ollama_base_url,
            "ollama_model": base_settings.ollama_model,
        }

    def _initialize_from_env(self) -> Dict[str, Any]:
        """
        Initialize runtime config from environment variables.
        从环境变量初始化运行时配置。

        Reads current values from env and persists them to Neo4j
        (if available) for future use.

        Returns:
            Dict with initial configuration values / 初始配置值字典
        """
        config = self._get_env_config()

        # Save to Neo4j if it's initialized / 如果 Neo4j 已初始化则保存
        if neo4j_client._initialized:
            self.update_runtime_config(config)
        return config

    def update_runtime_config(self, config: Dict[str, Any]) -> bool:
        """
        Update runtime configuration in Neo4j.
        更新 Neo4j 中的运行时配置。

        Applies a MERGE operation to create or update the single
        RuntimeConfig node. Filters out None values and "***" placeholders.

        Args:
            config:  Dict with configuration values to update
                    / 待更新的配置值字典

        Returns:
            True if the update was successful, False otherwise
            更新成功返回 True，否则返回 False
        """
        # Skip save if Neo4j is not initialized / 如果 Neo4j 未初始化则跳过
        if not neo4j_client._initialized:
            return False

        # Filter out None values and "***" placeholders (masked keys)
        # 过滤掉 None 值和 "***" 占位符（已掩码的密钥）
        filtered_config = {
            k: v
            for k, v in config.items()
            if v is not None and v != "***"
        }

        try:
            query = """
            MERGE (config:RuntimeConfig {id: $config_id})
            SET config += $properties,
                config.updated_at = datetime()
            RETURN config
            """
            result = neo4j_client.execute_query(
                query,
                {
                    "config_id": self.CONFIG_NODE_ID,
                    "properties": filtered_config,
                },
            )

            return len(result) > 0
        except RuntimeError:
            return False

    def get_ai_provider_config(self) -> Dict[str, Any]:
        """
        Get the current AI provider configuration.
        获取当前 AI 提供商的配置。

        Resolves the final configuration for the active AI provider by:
        1. Using the new universal config keys (ai_*) first
        2. Falling back to legacy provider-specific keys (openai_*, ollama_*)
        3. Using defaults from base_settings if nothing is set

        Returns:
            Dict with provider, api_key, model, base_url
            包含提供商、API密钥、模型、API地址的字典
        """
        runtime_config = self.get_runtime_config()
        provider = runtime_config.get("ai_provider", "mock")

        # Prefer universal config keys / 优先使用通用配置
        api_key = runtime_config.get("ai_api_key")
        model = runtime_config.get("ai_model")
        base_url = runtime_config.get("ai_base_url")

        # Backward compatibility: fall back to legacy keys
        # 向后兼容：回退到遗留配置
        if provider == "openai" and not api_key:
            api_key = runtime_config.get("openai_api_key")
            model = model or runtime_config.get("openai_model")
            base_url = base_url or runtime_config.get("openai_base_url")
        elif provider == "ollama" and not base_url:
            base_url = runtime_config.get("ollama_base_url")
            model = model or runtime_config.get("ollama_model")

        return {
            "provider": provider,
            "api_key": api_key,
            "model": model,
            "base_url": base_url,
        }


# Global singleton instance / 全局单例实例
config_service = ConfigService()
