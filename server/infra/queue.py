"""Redis Queue (RQ) — 连接池、重试、健康检查、命名空间。"""
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urlunparse

import redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from rq import Queue, Connection, Worker
from rq.job import Job
from rq import get_current_job

from infra.config import settings

logger = logging.getLogger(__name__)

# ── 连接池（进程级复用）──────────────────────────────────────────
_pool: Optional[redis.ConnectionPool] = None


def _build_redis_url() -> str:
    """构建 Redis URL，自动注入密码（如果单独配置了 REDIS_PASSWORD）。"""
    url = settings.redis_url
    if settings.redis_password and '@' not in urlparse(url).netloc:
        parsed = urlparse(url)
        netloc = f":{settings.redis_password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        url = urlunparse(parsed._replace(netloc=netloc))
    return url


def _get_connection_pool() -> redis.ConnectionPool:
    """获取或创建 Redis 连接池（懒加载 + 进程级单例）。"""
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
            # 注意：health_check_interval 在 redis-py 5.x 中可能与 CLIENT SETINFO
            # 产生递归调用。改用应用层 ping 检测。decode_responses=False，
            # 因为 RQ 需要二进制协议存储 pickle 数据。
            decode_responses=False,
        )
        logger.info("Redis 连接池已创建: %s (max_connections=%d)", redis_url, settings.redis_max_connections)
    return _pool


def _make_key(*parts: str) -> str:
    """生成带命名空间前缀的 key。"""
    return ":".join([settings.redis_key_prefix, *parts])


# ── RedisQueue ────────────────────────────────────────────────────


class RedisQueue:
    """Redis 队列客户端 — 连接池 + 自动重试 + 优雅降级。"""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._connected = False
        self.redis_conn: Optional[redis.Redis] = None
        self.queue: Optional[Queue] = None
        self._connect()

    # ── 连接管理 ────────────────────────────────────────────────

    def _connect(self) -> None:
        """建立 Redis 连接（使用连接池 + 重试）。"""
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
                logger.warning("Redis 连接失败 (第 %d/%d 次): %s", attempt, max_retries, e)
                if attempt < max_retries:
                    time.sleep(1.0 * attempt)
                else:
                    logger.warning("Redis 不可用，降级为内存存储")
                    self._connected = False
                    self.redis_conn = None
                    self.queue = None

    def is_connected(self) -> bool:
        """Redis 是否已连接且可用。"""
        if not self._connected or not self.redis_conn:
            return False
        try:
            self.redis_conn.ping()
            return True
        except RedisError:
            self._connected = False
            return False

    def health_check(self) -> Dict[str, Any]:
        """健康检查 — 返回 Redis 状态信息，供 API 端点使用。"""
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

            # info() 返回 bytes key，需要解码
            def _decode_info(raw: dict) -> dict:
                return {k.decode() if isinstance(k, bytes) else k: v for k, v in raw.items()}

            info = _decode_info(self.redis_conn.info(section="server"))
            memory = _decode_info(self.redis_conn.info(section="memory"))
            stats = _decode_info(self.redis_conn.info(section="stats"))

            result.update({
                "connected": pong,
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_days": info.get("uptime_in_days", 0),
                "used_memory_human": memory.get("used_memory_human", "0"),
                "used_memory_peak_human": memory.get("used_memory_peak_human", "0"),
                "connected_clients": stats.get("connected_clients", 0),
                "total_connections_received": stats.get("total_connections_received", 0),
                "keyspace_hits": stats.get("keyspace_hits", 0),
                "keyspace_misses": stats.get("keyspace_misses", 0),
                "hit_rate": round(
                    int(stats.get("keyspace_hits", 0)) / max(int(stats.get("keyspace_hits", 0)) + int(stats.get("keyspace_misses", 0)), 1) * 100, 1
                ) if (int(stats.get("keyspace_hits", 0)) + int(stats.get("keyspace_misses", 0))) > 0 else 0,
            })

            # 统计当前命名空间下的 key 数量
            pattern = _make_key("*")
            keys = self.redis_conn.keys(pattern)
            result["namespace_keys"] = len(keys)
        except RedisError as e:
            result["error"] = str(e)
            self._connected = False

        return result

    # ── 队列操作 ────────────────────────────────────────────────

    def enqueue(self, func, *args, **kwargs) -> Optional[Job]:
        """入队任务。"""
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
        """根据 ID 获取任务。"""
        if not self.is_connected():
            return None
        try:
            return Job.fetch(job_id, connection=self.redis_conn)
        except Exception:
            return None

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取任务状态详情。"""
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
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            }

            if job.is_finished:
                result["result"] = job.result
            if job.is_failed:
                result["error"] = str(job.exc_info) if job.exc_info else "未知错误"
            if hasattr(job, 'meta') and job.meta:
                result.update(job.meta)

            return result
        except Exception as e:
            return {"status": "not_found", "error": str(e)}

    def cancel_job(self, job_id: str) -> bool:
        """取消任务（支持运行中任务的中断信号）。"""
        if not self.is_connected():
            return False
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            if job.get_status() in ('queued', 'started', 'deferred', 'scheduled'):
                if job.get_status() == 'started':
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

    # ── 缓存辅助方法 ────────────────────────────────────────────

    def cache_get(self, key: str) -> Optional[str]:
        """从缓存读取（带命名空间前缀，自动解码 bytes）。"""
        if not self.is_connected():
            return None
        try:
            val = self.redis_conn.get(_make_key(key))
            return val.decode() if isinstance(val, bytes) else val
        except RedisError:
            return None

    def cache_set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """写入缓存（带命名空间前缀 + TTL）。"""
        if not self.is_connected():
            return False
        try:
            ttl = ttl if ttl is not None else settings.redis_default_ttl
            return bool(self.redis_conn.setex(_make_key(key), ttl, value))
        except RedisError:
            return False

    def cache_delete(self, key: str) -> bool:
        """删除缓存 key。"""
        if not self.is_connected():
            return False
        try:
            return bool(self.redis_conn.delete(_make_key(key)))
        except RedisError:
            return False

    def cache_flush_namespace(self) -> int:
        """清空当前命名空间下所有 key，返回删除数。"""
        if not self.is_connected():
            return 0
        try:
            keys = self.redis_conn.keys(_make_key("*"))
            if keys:
                return self.redis_conn.delete(*keys)
        except RedisError:
            pass
        return 0


# ── 全局实例 ──────────────────────────────────────────────────────
_queue_instance: Optional[RedisQueue] = None


def get_queue() -> RedisQueue:
    """获取全局 RedisQueue 实例（懒加载）。"""
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = RedisQueue()
    return _queue_instance


# ── Worker 工具函数 ───────────────────────────────────────────────


def update_job_progress(progress: int, message: str, **kwargs) -> None:
    """
    在 Worker 中更新任务进度。

    用法（在 RQ worker task 内）:
        update_job_progress(50, "正在提取实体...", chunks=12, entities=45)
    """
    job = get_current_job()
    if job:
        meta = job.meta or {}
        meta.update({"progress": progress, "message": message, **kwargs})
        job.meta = meta
        job.save()
