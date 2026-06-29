"""
Redis Queue (RQ) — Connection pooling, retry, health check, namespace isolation
===============================================================================

Redis 队列模块 — 支持连接池、自动重试、健康检查和命名空间隔离。

Provides a robust Redis-backed task queue using RQ (Redis Queue). Features:
- Connection pooling with retry logic / 带重试逻辑的连接池
- Graceful degradation to in-memory fallback when Redis unavailable / Redis不可用时的优雅降级
- Health check endpoint support / 健康检查端点支持
- Namespaced cache helpers / 带命名空间的缓存辅助方法
- Worker progress tracking / Worker 进度追踪

Architecture / 架构说明::

    get_queue()  →  RedisQueue (singleton, lazy-loaded)
                       │
                       ├── is_connected()  →  ping check / 心跳检测
                       ├── enqueue()       →  RQ Queue / 入队
                       ├── get_job_status() →  Job status / 任务状态
                       ├── cancel_job()    →  Cancel with meta signal / 取消
                       └── cache_*()       →  Namespaced helpers / 缓存

Fallback strategy / 降级策略::
    1. Redis available → use RQ Queue with connection pool
    2. Redis unavailable → return None; caller uses in-memory fallback
"""
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse

import redis
from redis.exceptions import (
    RedisError,
    ConnectionError as RedisConnectionError,
    TimeoutError as RedisTimeoutError,
)
from rq import Queue, Connection, Worker
from rq.job import Job
from rq import get_current_job

from server.infra.config import settings

logger = logging.getLogger(__name__)

# ── Connection pool (process-level singleton) ──────────────────────────
# ── 连接池（进程级单例复用）────────────────────────────────────────────
_pool: Optional[redis.ConnectionPool] = None


def _build_redis_url() -> str:
    """
    Build Redis URL, automatically injecting password if configured separately.
    构建 Redis URL，如果单独配置了 REDIS_PASSWORD 则自动注入密码。

    Handles the case where the base URL doesn't contain credentials but a
    separate password configuration is provided via redis_password setting.

    Returns:
        Complete Redis URL with embedded authentication / 包含认证信息的完整 URL
    """
    url = settings.redis_url
    if settings.redis_password and '@' not in urlparse(url).netloc:
        parsed = urlparse(url)
        netloc = f":{settings.redis_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        url = urlunparse(parsed._replace(netloc=netloc))
    return url


def _get_connection_pool() -> redis.ConnectionPool:
    """
    Get or create the Redis connection pool (lazy-loaded, process-level singleton).
    获取或创建 Redis 连接池（懒加载，进程级单例）。

    The pool is configured with the connection parameters from settings,
    including socket timeouts and retry behavior. decode_responses=False is
    critical because RQ uses the binary protocol for pickle serialization.

    Returns:
        Shared Redis connection pool / 共享的 Redis 连接池
    """
    global _pool
    if _pool is None:
        redis_url = _build_redis_url()
        _pool = redis.ConnectionPool.from_url(
            redis_url,
            db=settings.redis_db,
            max_connections=settings.redis_max_connections,
            socket_timeout=settings.redis_socket_timeout,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            retry_on_timeout=settings.redis_retry_on_timeout,
            # NOTE: health_check_interval in redis-py 5.x may cause recursive
            # calls with CLIENT SETINFO. We use application-layer ping instead.
            # decode_responses=False is critical for RQ binary protocol.
            decode_responses=False,
        )
        logger.info(
            "Redis 连接池已创建: %s (max_connections=%d)",
            redis_url,
            settings.redis_max_connections,
        )
    return _pool


def _make_key(*parts: str) -> str:
    """
    Generate a namespaced Redis key.
    生成带命名空间前缀的 Redis key。

    Prevents key collision between different applications sharing the same
    Redis instance.

    Args:
        parts:  Key path components / key 路径组件

    Returns:
        Namespaced key string (e.g., "graphforge:job:123")
    """
    return ":".join([settings.redis_key_prefix, *parts])


# ── RedisQueue ────────────────────────────────────────────────────


class RedisQueue:
    """
    Redis Queue client with connection pooling, auto-retry, and graceful degradation.
    Redis 队列客户端 — 连接池 + 自动重试 + 优雅降级。

    Provides both job queue operations (enqueue, status, cancel) and general
    cache operations (get, set, delete, flush) with automatic namespace prefixing.

    When Redis is unavailable, all operations gracefully return None/False,
    allowing callers to use in-memory alternatives without errors.
    当 Redis 不可用时，所有操作优雅地返回 None/False。

    Attributes:
        redis_url:    Connection URL / 连接 URL
        redis_conn:   Redis connection instance / Redis 连接实例
        queue:        RQ Queue instance / RQ 队列实例
        _connected:   Internal connectivity flag / 内部连接状态标志
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._connected = False
        self.redis_conn: Optional[redis.Redis] = None
        self.queue: Optional[Queue] = None
        self._connect()

    # ── Connection management / 连接管理 ─────────────────────────────

    def _connect(self) -> None:
        """
        Establish Redis connection with connection pool and retry.
        建立 Redis 连接（使用连接池 + 重试）。

        Retries up to 3 times with exponential backoff (1s, 2s, 3s).
        If all retries fail, sets _connected=False for graceful degradation.
        """
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                pool = _get_connection_pool()
                self.redis_conn = redis.Redis(connection_pool=pool)
                self.redis_conn.ping()
                self.queue = Queue(connection=self.redis_conn, name='default')
                self._connected = True
                logger.info("Redis 连接成功: %s", self.redis_url)
                return
            except (RedisConnectionError, RedisTimeoutError, OSError) as e:
                logger.warning(
                    "Redis 连接失败 (第 %d/%d 次): %s",
                    attempt, max_retries, e
                )
                if attempt < max_retries:
                    time.sleep(1.0 * attempt)
                else:
                    logger.warning("Redis 不可用，降级为内存存储")
                    self._connected = False
                    self.redis_conn = None
                    self.queue = None

    def is_connected(self) -> bool:
        """
        Check if Redis is connected and available.
        检查 Redis 是否已连接且可用。

        Performs a lightweight PING to verify the connection is still alive.
        If PING fails, marks the connection as disconnected.

        Returns:
            True if Redis is reachable / Redis 可达则返回 True
        """
        if not self._connected or not self.redis_conn:
            return False
        try:
            self.redis_conn.ping()
            return True
        except RedisError:
            self._connected = False
            return False

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive Redis health check for API endpoints.
        执行全面的 Redis 健康检查，供 API 端点使用。

        Returns detailed Redis server information including version, memory
        usage, hit rate, and namespace-specific key counts.

        Returns:
            Dictionary with health status and metrics / 包含健康状态和指标的字典
        """
        result: Dict[str, Any] = {
            "connected": False,
            "url": self.redis_url,
            "prefix": settings.redis_key_prefix,
            "db": settings.redis_db,
        }
        if not self.redis_conn:
            result["error"] = "Redis 客户端未初始化"
            return result

        try:
            pong = self.redis_conn.ping()

            # info() returns bytes keys — decode them
            def _decode_info(raw: dict) -> dict:
                return {
                    k.decode() if isinstance(k, bytes) else k: v
                    for k, v in raw.items()
                }

            info = _decode_info(self.redis_conn.info(section="server"))
            memory = _decode_info(self.redis_conn.info(section="memory"))
            stats = _decode_info(self.redis_conn.info(section="stats"))

            keyspace_hits = int(stats.get("keyspace_hits", 0))
            keyspace_misses = int(stats.get("keyspace_misses", 0))
            total_ops = keyspace_hits + keyspace_misses

            result.update({
                "connected": pong,
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_days": info.get("uptime_in_days", 0),
                "used_memory_human": memory.get("used_memory_human", "0"),
                "used_memory_peak_human": memory.get(
                    "used_memory_peak_human", "0"
                ),
                "connected_clients": stats.get("connected_clients", 0),
                "total_connections_received": stats.get(
                    "total_connections_received", 0
                ),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses,
                "hit_rate": round(
                    keyspace_hits / max(total_ops, 1) * 100, 1
                ),
            })

            # Count keys under our namespace / 统计当前命名空间下的 key 数量
            pattern = _make_key("*")
            keys = self.redis_conn.keys(pattern)
            result["namespace_keys"] = len(keys)
        except RedisError as e:
            result["error"] = str(e)
            self._connected = False

        return result

    # ── Queue operations / 队列操作 ─────────────────────────────────

    def enqueue(self, func, *args, **kwargs) -> Optional[Job]:
        """
        Enqueue a task for background processing.
        将任务加入后台处理队列。

        Extracts RQ-specific kwargs (job_timeout, result_ttl) from the kwargs
        dict before forwarding to RQ's enqueue.

        Args:
            func:       Function to execute in background / 后台执行的函数
            *args:      Positional arguments for the function / 位置参数
            **kwargs:   Keyword arguments, including RQ-specific ones
                       / 关键字参数（包括 RQ 专用参数）

        Returns:
            RQ Job object if successful, None if Redis is unavailable
            成功返回 RQ Job 对象，Redis 不可用时返回 None
        """
        if not self.is_connected():
            return None
        try:
            job_timeout = kwargs.pop('job_timeout', '1h')
            result_ttl = kwargs.pop('result_ttl', settings.redis_default_ttl)
            job = self.queue.enqueue(
                func, *args, **kwargs,
                job_timeout=job_timeout,
                result_ttl=result_ttl,
            )
            return job
        except RedisError as e:
            logger.error("入队失败: %s", e)
            return None

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Fetch a job by its ID.
        根据 ID 获取任务。

        Args:
            job_id:  RQ Job ID / RQ 任务 ID

        Returns:
            RQ Job object or None if not found / Job 对象或 None
        """
        if not self.is_connected():
            return None
        try:
            return Job.fetch(job_id, connection=self.redis_conn)
        except Exception:
            return None

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get detailed job status with progress metadata.
        获取任务详细状态，包括进度元数据。

        Maps RQ internal statuses to application-level statuses:
        - queued/scheduled/deferred → "queued"
        - started → "processing"
        - finished → "completed"
        - failed → "failed"

        If the job is not found, returns {"status": "not_found"}.

        Args:
            job_id:  RQ Job ID / RQ 任务 ID

        Returns:
            Dictionary with status, timestamps, and job meta / 包含状态、时间戳和元数据的字典
        """
        if not self.is_connected():
            return {"status": "unknown", "error": "Redis 未连接"}

        try:
            job = Job.fetch(job_id, connection=self.redis_conn)

            status_map = {
                'queued': 'queued',
                'started': 'processing',
                'finished': 'completed',
                'failed': 'failed',
                'deferred': 'queued',
                'scheduled': 'queued',
                'canceled': 'cancelled',
            }

            result: Dict[str, Any] = {
                "status": status_map.get(job.get_status(), 'unknown'),
                "jobId": job.id,
                "created_at": (
                    job.created_at.isoformat() if job.created_at else None
                ),
                "started_at": (
                    job.started_at.isoformat() if job.started_at else None
                ),
                "ended_at": (
                    job.ended_at.isoformat() if job.ended_at else None
                ),
            }

            if job.is_finished:
                result["result"] = job.result
            if job.is_failed:
                result["error"] = (
                    str(job.exc_info) if job.exc_info else "未知错误"
                )
            if hasattr(job, 'meta') and job.meta:
                result.update(job.meta)

            return result
        except Exception as e:
            return {"status": "not_found", "error": str(e)}

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running or queued job.
        取消一个正在运行或等待中的任务。

        For running jobs, sets a '_cancelled' flag in the job meta so the
        worker process can detect it and abort. For queued jobs, directly
        cancels via RQ's cancel().

        Args:
            job_id:  RQ Job ID to cancel / 要取消的 RQ 任务 ID

        Returns:
            True if cancellation was successful, False otherwise
            成功返回 True，否则返回 False
        """
        if not self.is_connected():
            return False
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.get_status() in ('queued', 'started', 'deferred', 'scheduled'):
                if job.get_status() == 'started':
                    # For running jobs: set cancellation signal in meta
                    meta = job.meta or {}
                    meta['_cancelled'] = True
                    meta['status'] = 'cancelled'
                    meta['message'] = '任务已被用户取消'
                    job.meta = meta
                    job.save()
                job.cancel()
                return True
            return False
        except Exception as e:
            logger.warning("取消任务 %s 失败: %s", job_id, e)
            return False

    # ── Cache helper methods / 缓存辅助方法 ─────────────────────────

    def cache_get(self, key: str) -> Optional[str]:
        """
        Read from cache with automatic namespace prefixing.
        从缓存读取（自动添加命名空间前缀）。

        Args:
            key:  Cache key (without prefix) / 缓存 key（无前缀）

        Returns:
            String value or None if key not found / 字符串值或 None
        """
        if not self.is_connected():
            return None
        try:
            val = self.redis_conn.get(_make_key(key))
            return val.decode() if isinstance(val, bytes) else val
        except RedisError:
            return None

    def cache_set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """
        Write to cache with automatic namespace prefixing and TTL.
        写入缓存（自动添加命名空间前缀和 TTL）。

        Args:
            key:    Cache key (without prefix) / 缓存 key
            value:  String value to store / 要存储的字符串值
            ttl:    TTL in seconds (default from settings, 24h) / 过期时间

        Returns:
            True on success, False on failure / 成功返回 True
        """
        if not self.is_connected():
            return False
        try:
            ttl = ttl if ttl is not None else settings.redis_default_ttl
            return bool(self.redis_conn.setex(_make_key(key), ttl, value))
        except RedisError:
            return False

    def cache_delete(self, key: str) -> bool:
        """
        Delete a cache key.
        删除缓存 key。

        Args:
            key:  Cache key (without prefix) / 缓存 key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self.is_connected():
            return False
        try:
            return bool(self.redis_conn.delete(_make_key(key)))
        except RedisError:
            return False

    def cache_flush_namespace(self) -> int:
        """
        Flush all keys under the current namespace.
        清空当前命名空间下所有 key。

        Uses pattern matching to find all keys with the current prefix
        and deletes them in a batch.

        Returns:
            Number of deleted keys / 删除的 key 数量
        """
        if not self.is_connected():
            return 0
        try:
            keys = self.redis_conn.keys(_make_key("*"))
            if keys:
                return self.redis_conn.delete(*keys)
        except RedisError:
            pass
        return 0


# ── Global singleton instance / 全局单例实例 ─────────────────────────
_queue_instance: Optional[RedisQueue] = None


def get_queue() -> RedisQueue:
    """
    Get the global RedisQueue instance (lazy-loaded singleton).
    获取全局 RedisQueue 实例（懒加载单例）。

    Returns:
        Shared RedisQueue instance / 共享的 RedisQueue 实例
    """
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = RedisQueue()
    return _queue_instance


# ── Worker utility function / Worker 工具函数 ─────────────────────────


def update_job_progress(progress: int, message: str, **kwargs) -> None:
    """
    Update job progress from within an RQ worker task.
    在 RQ Worker 任务中更新任务进度。

    This function should only be called inside an RQ worker context.
    Outside a worker, it silently does nothing.

    Usage / 用法::

        # Inside an RQ worker task:
        update_job_progress(50, "Extracting entities...", chunks=12, entities=45)

    Args:
        progress:  Progress percentage (0-100) / 进度百分比（0-100）
        message:   Status message / 状态消息
        **kwargs:  Additional metadata to store / 附加的元数据
    """
    job = get_current_job()
    if job:
        meta = job.meta or {}
        meta.update({"progress": progress, "message": message, **kwargs})
        job.meta = meta
        job.save()
