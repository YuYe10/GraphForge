"""
Neo4j Graph Database Client
============================

Neo4j 图数据库客户端，提供连接管理、模式初始化和 CRUD 操作。

Provides a comprehensive Neo4j client with:
- Connection management with retry logic / 带重试的连接管理
- Schema initialization (constraints, indexes) / 模式初始化（约束、索引）
- Type conversion (Neo4j DateTime → Python str for JSON serialization) / 类型转换
- Property sanitization (nesting pruned to primitives for Neo4j) / 属性清理
- Document, Concept, Topic, Relationship CRUD / 完整的 CRUD 操作
- Bilingual concept search (Chinese + English) / 双语概念搜索
- Recursive orphan node cleanup / 递归孤立节点清理

Architecture / 架构说明::

    neo4j_client = Neo4jClient()  ← Global singleton / 全局单例
                        │
                        ├── initialize()     → Connect + schema setup
                        ├── execute_query()  → Generic Cypher execution
                        ├── create_document()   → Document CRUD
                        ├── create_concept()    → Concept CRUD
                        ├── create_relationship() → Edge CRUD
                        ├── delete_document()  → Cascade delete
                        └── find_similar_concepts() → Bilingual search
"""
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from neo4j.exceptions import ServiceUnavailable
from server.infra.config import settings


class Neo4jClient:
    """
    Neo4j database client with connection pooling, schema init, and type conversion.
    Neo4j 数据库客户端，支持连接池、模式初始化和类型转换。

    This is a low-level client that provides direct Cypher query execution
    and convenience methods for common graph operations. All queries return
    plain Python dicts with Neo4j-specific types (DateTime, Node, etc.)
    automatically converted to JSON-serializable Python types.

    Usage / 用法示例::

        client = Neo4jClient()
        client.initialize()  # Must call before execute_query / 必须在使用前调用

        # Query example / 查询示例
        results = client.execute_query(
            "MATCH (c:Concept {name: $name}) RETURN c",
            {"name": "AI"}
        )

    Attributes:
        driver:         Neo4j Bolt driver instance / Neo4j Bolt 驱动实例
        _initialized:   Whether the client has been initialized / 是否已初始化
    """

    def __init__(self):
        self.driver: Optional[Driver] = None
        self._initialized = False

    def initialize(self):
        """
        Initialize connection and schema.
        初始化连接和数据库模式。

        This must be called explicitly before any query execution (typically
        during application startup). It:
        1. Establishes a Bolt connection with retry logic
        2. Initializes database schema (constraints + indexes)
        3. Marks the client as initialized

        Raises:
            ConnectionError: If connection fails after all retries
        """
        if not self._initialized:
            self._connect()
            self._initialize_schema()
            self._initialized = True

    def _connect(self, max_retries: int = 30, retry_delay: float = 2.0):
        """
        Establish connection to Neo4j with retry logic.
        建立到 Neo4j 的连接，带重试逻辑。

        Distinguishes between authentication errors (immediate failure) and
        connection errors (retryable). Neo4j may take time to start up,
        especially in Docker environments, so we retry generously.

        Args:
            max_retries:  Maximum number of connection attempts (default: 30)
            retry_delay:  Delay in seconds between retries (default: 2.0)

        Raises:
            ConnectionError: On authentication failure or max retry exhaustion
        """
        for attempt in range(max_retries):
            try:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_pass)
                )
                # Verify connection & identify current user
                # 验证连接并识别当前用户
                with self.driver.session() as session:
                    result = session.run("SHOW CURRENT USER")
                    current_user = result.single()["user"]
                print(
                    f"✅ Neo4j connected as '{current_user}' @ "
                    f"{settings.neo4j_uri} (attempt {attempt + 1})"
                )
                return
            except (ServiceUnavailable, OSError, Exception) as e:
                # Authentication errors are non-retryable / 认证错误不可重试
                error_str = str(e).lower()
                if any(
                    keyword in error_str
                    for keyword in [
                        "authentication", "auth", "unauthorized",
                        "invalid credentials",
                    ]
                ):
                    raise ConnectionError(f"Neo4j authentication failed: {e}")

                # Connection errors are retryable / 连接错误可重试
                if attempt < max_retries - 1:
                    print(
                        f"⏳ Waiting for Neo4j Bolt to be ready... "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(
                        f"Failed to connect to Neo4j after {max_retries} "
                        f"attempts. Last error: {e}"
                    )

    def _initialize_schema(self):
        """
        Initialize database schema: constraints and indexes.
        初始化数据库模式：约束和索引。

        Schema initialization has two paths:
        1. Primary: Load from schema.cypher file (if it exists alongside this module)
           / 优先：从 schema.cypher 文件加载
        2. Fallback: Use inline Cypher statements (backward compatibility)
           / 后备：使用内联 Cypher 语句

        This approach allows schema management via version-controlled Cypher files
        while maintaining compatibility with existing deployments.
        """
        # Prefer schema.cypher file if it exists / 优先使用 schema.cypher 文件
        schema_file = Path(__file__).parent / "schema.cypher"

        if schema_file.exists():
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_cypher = f.read()

                # Split into statements, preserving CALL statement integrity
                # 分割为多个语句，保留 CALL 语句的完整性
                statements = []
                current_statement = []
                in_call = False

                for line in schema_cypher.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue

                    current_statement.append(line)

                    if line.upper().startswith("CALL"):
                        in_call = True
                    elif in_call and (
                        "RETURN" in line.upper() or line.endswith(";")
                    ):
                        in_call = False
                        if line.endswith(";"):
                            stmt = " ".join(current_statement).rstrip(";")
                            if stmt:
                                statements.append(stmt)
                            current_statement = []
                    elif line.endswith(";") and not in_call:
                        stmt = " ".join(current_statement).rstrip(";")
                        if stmt:
                            statements.append(stmt)
                        current_statement = []

                # Handle last statement / 处理最后一个语句
                if current_statement:
                    stmt = " ".join(current_statement).rstrip(";")
                    if stmt:
                        statements.append(stmt)

                with self.driver.session() as session:
                    for statement in statements:
                        if statement.strip():
                            try:
                                result = session.run(statement)
                                # Consume CALL results / 消费 CALL 语句的结果
                                if "CALL" in statement.upper():
                                    list(result)
                            except Exception as e:
                                error_msg = str(e).lower()
                                # Skip "already exists" errors for idempotency
                                if any(
                                    keyword in error_msg
                                    for keyword in [
                                        "already exists",
                                        "equivalent index already exists",
                                        "index with name",
                                        "an equivalent index already exists",
                                        "constraint already exists",
                                    ]
                                ):
                                    continue
                                # Log but don't block initialization for syntax issues
                                print(
                                    f"Warning: Failed to execute schema "
                                    f"statement: {e}"
                                )
                                print(
                                    f"Statement: {statement[:100]}..."
                                )
                    print("Schema initialized from schema.cypher")
            except Exception as e:
                print(
                    f"Warning: Failed to load schema.cypher, falling back "
                    f"to inline schema: {e}"
                )
                self._initialize_schema_inline()
        else:
            # Fallback: inline schema (backward compatible)
            # 后备方案：内联模式（向后兼容）
            self._initialize_schema_inline()

    def _initialize_schema_inline(self):
        """
        Initialize schema using inline Cypher (backward compatibility).
        使用内联 Cypher 初始化模式（向后兼容）。

        Creates the minimum required constraints and indexes for operation.
        """
        with self.driver.session() as session:
            # Unique constraints for node types / 节点类型唯一约束
            session.run("""
                CREATE CONSTRAINT document_checksum_unique IF NOT EXISTS
                FOR (d:Document) REQUIRE d.checksum IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT concept_name_unique IF NOT EXISTS
                FOR (c:Concept) REQUIRE c.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT topic_name_unique IF NOT EXISTS
                FOR (t:Topic) REQUIRE t.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT runtime_config_id_unique IF NOT EXISTS
                FOR (r:RuntimeConfig) REQUIRE r.id IS UNIQUE
            """)

            # Indexes for common query patterns / 常用查询模式索引
            session.run("""
                CREATE INDEX source_hash IF NOT EXISTS
                FOR (s:Source) ON (s.hash)
            """)
            session.run("""
                CREATE INDEX concept_domain IF NOT EXISTS
                FOR (c:Concept) ON (c.domain)
            """)
            session.run("""
                CREATE INDEX document_kind IF NOT EXISTS
                FOR (d:Document) ON (d.kind)
            """)

    def close(self):
        """
        Close the driver connection gracefully.
        优雅地关闭驱动连接。
        """
        if self.driver:
            self.driver.close()

    # ══════════════════════════════════════════════════════════════
    # Type Conversion Utilities / 类型转换工具
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _sanitize_properties(props: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize properties to only include primitive types and arrays.
        清理属性，仅保留原始类型和数组。

        Neo4j property values can only be primitives (str, int, float, bool)
        or arrays of primitives. Nested dicts, objects, and other complex
        types must be serialized to JSON strings.

        Args:
            props:  Dictionary of properties to sanitize / 待清理的属性字典

        Returns:
            Sanitized dictionary with only Neo4j-compatible types
            仅包含 Neo4j 兼容类型的清理后字典
        """
        if not props:
            return {}

        sanitized = {}
        for key, value in props.items():
            if value is None:
                continue
            # Primitives allowed directly / 原始类型直接保留
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            # Arrays of primitives allowed / 原始类型数组允许
            elif isinstance(value, (list, tuple)):
                try:
                    sanitized[key] = [
                        v
                        for v in value
                        if isinstance(v, (str, int, float, bool, type(None)))
                    ]
                except Exception:
                    pass
            # Dicts serialized to JSON strings / 字典序列化为 JSON 字符串
            elif isinstance(value, dict):
                try:
                    sanitized[key] = json.dumps(
                        value, default=str, ensure_ascii=False
                    )
                except Exception:
                    pass
            # Other types converted to string / 其他类型转为字符串
            else:
                try:
                    sanitized[key] = str(value)
                except Exception:
                    pass

        return sanitized

    @staticmethod
    def _convert_neo4j_types(obj: Any) -> Any:
        """
        Recursively convert Neo4j special types to standard Python types.
        递归地将 Neo4j 特殊类型转换为标准 Python 类型。

        Neo4j driver returns special types (DateTime, Date, Time, Duration,
        Node, Relationship) that are not JSON-serializable. This method
        converts them to standard Python equivalents (ISO strings, dicts).

        Supported conversions / 支持的转换::

            Neo4j DateTime  →  ISO format string (via .to_native())
            Neo4j Date      →  ISO format string
            Neo4j Time      →  ISO format string
            Neo4j Duration  →  String representation
            Neo4j Node      →  Dict of properties
            Neo4j Relationship  →  Dict of properties

        Args:
            obj:  Object to convert (dict, list, Node, Relationship, or primitive)

        Returns:
            Converted object with all Neo4j types replaced by Python equivalents
        """
        try:
            from neo4j.time import DateTime, Date, Time, Duration
            from neo4j.graph import Node, Relationship
        except ImportError:
            return obj

        if obj is None:
            return None

        # Neo4j Node → dict of properties / 节点 → 属性字典
        if isinstance(obj, Node):
            return Neo4jClient._convert_neo4j_types(dict(obj))

        # Neo4j Relationship → dict of properties / 关系 → 属性字典
        if isinstance(obj, Relationship):
            return Neo4jClient._convert_neo4j_types(dict(obj))

        # Neo4j datetime types → ISO strings / 日期时间 → ISO 字符串
        if isinstance(obj, (DateTime, Date, Time)):
            native = obj.to_native()
            return (
                native.isoformat()
                if hasattr(native, 'isoformat')
                else str(native)
            )
        if isinstance(obj, Duration):
            return str(obj)

        # Dict: recursively convert values / 字典：递归转换值
        if isinstance(obj, dict):
            return {
                k: Neo4jClient._convert_neo4j_types(v)
                for k, v in obj.items()
            }

        # List/tuple: recursively convert elements / 列表：递归转换元素
        if isinstance(obj, (list, tuple)):
            return [Neo4jClient._convert_neo4j_types(item) for item in obj]

        return obj

    # ══════════════════════════════════════════════════════════════
    # Core Query Execution / 核心查询执行
    # ══════════════════════════════════════════════════════════════

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        执行 Cypher 查询并返回结果。

        All Neo4j types in results are automatically converted to JSON-serializable
        Python types via _convert_neo4j_types().

        Args:
            query:        Cypher query string / Cypher 查询语句
            parameters:   Query parameters (use $param syntax in query)
                         / 查询参数

        Returns:
            List of result records as Python dicts
            结果记录列表，以 Python 字典形式返回

        Raises:
            RuntimeError: If client is not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "Neo4jClient is not initialized. Call initialize() first."
            )

        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [
                self._convert_neo4j_types(dict(record)) for record in result
            ]

    # ══════════════════════════════════════════════════════════════
    # Document CRUD / 文档 CRUD
    # ══════════════════════════════════════════════════════════════

    def create_document(
        self,
        doc_id: str,
        filename: str,
        checksum: str,
        kind: str,
        size: int,
        mime: Optional[str] = None,
        source_id: Optional[str] = None,
        meta: Optional[Dict] = None,
    ) -> bool:
        """
        Create or update a Document node (MERGE by ID).
        创建或更新 Document 节点（按 ID 合并）。

        The meta dict is serialized to a JSON string internally since Neo4j
        does not natively support nested property objects.

        Args:
            doc_id:     Unique document ID / 唯一文档 ID
            filename:   Original filename / 原始文件名
            checksum:   SHA256 checksum for deduplication / 校验和
            kind:       Document type (pdf, md, txt, docx) / 文档类型
            size:       File size in bytes / 文件大小（字节）
            mime:       MIME type / MIME 类型
            source_id:  Optional source identifier / 可选来源标识
            meta:       Optional metadata dict (serialized to JSON) / 元数据字典

        Returns:
            True if the document was created/updated / 成功返回 True
        """
        # Serialize meta dict to JSON string for Neo4j storage
        meta_json = json.dumps(meta) if meta and len(meta) > 0 else None
        query = """
        MERGE (d:Document {id: $doc_id})
        SET d.filename = $filename,
            d.checksum = $checksum,
            d.kind = $kind,
            d.size = $size,
            d.mime = $mime,
            d.source_id = $source_id,
            d.meta = $meta_json,
            d.created_at = coalesce(d.created_at, datetime()),
            d.updated_at = datetime()
        RETURN d
        """
        result = self.execute_query(
            query,
            {
                "doc_id": doc_id,
                "filename": filename,
                "checksum": checksum,
                "kind": kind,
                "size": size,
                "mime": mime,
                "source_id": source_id,
                "meta_json": meta_json,
            },
        )
        return len(result) > 0

    def mark_document_processed(
        self, doc_id: str, status: str = "completed"
    ) -> bool:
        """
        Mark a document as processed with a status flag.
        标记文档的处理状态。

        Args:
            doc_id:  Document ID / 文档 ID
            status:  Processing status (e.g., "completed", "failed")
                    / 处理状态

        Returns:
            True if successful / 成功返回 True
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        SET d.processing_status = $status,
            d.updated_at = datetime()
        RETURN d
        """
        result = self.execute_query(
            query, {"doc_id": doc_id, "status": status}
        )
        return len(result) > 0

    # ══════════════════════════════════════════════════════════════
    # Concept CRUD / 概念 CRUD
    # ══════════════════════════════════════════════════════════════

    def create_concept(
        self,
        name: str,
        domain: Optional[str] = None,
        meta: Optional[Dict] = None,
    ) -> bool:
        """
        Create or merge a Concept node.
        创建或合并一个 Concept 节点 (MERGE by name).

        Uses MERGE to ensure idempotency — if a concept with the same name
        already exists, only the updated_at timestamp is touched.

        Args:
            name:    Concept name (used as unique identifier) / 概念名称（唯一标识）
            domain:  Knowledge domain / 知识领域
            meta:    Optional metadata (serialized to JSON) / 元数据

        Returns:
            True if successful / 成功返回 True
        """
        meta_json = json.dumps(meta) if meta and len(meta) > 0 else None
        query = """
        MERGE (c:Concept {name: $name})
        ON CREATE SET
            c.domain = $domain,
            c.meta = $meta_json,
            c.aliases = [],
            c.created_at = datetime(),
            c.updated_at = datetime()
        ON MATCH SET
            c.updated_at = datetime()
        RETURN c
        """
        result = self.execute_query(
            query,
            {"name": name, "domain": domain, "meta_json": meta_json},
        )
        return len(result) > 0

    def add_concept_alias(self, canonical_name: str, alias: str) -> bool:
        """
        Add an alias to an existing concept.
        为已有概念添加别名。

        Aliases are stored as a list property on the Concept node and are
        used for bilingual matching and fuzzy entity linking.

        Args:
            canonical_name:  The canonical concept name / 规范概念名称
            alias:           The alias to add / 要添加的别名

        Returns:
            True if successful / 成功返回 True
        """
        query = """
        MATCH (c:Concept {name: $canonical_name})
        SET c.aliases = coalesce(c.aliases, []) +
            CASE WHEN $alias IN coalesce(c.aliases, [])
                 THEN []
                 ELSE [$alias]
            END,
            c.updated_at = datetime()
        RETURN c
        """
        result = self.execute_query(
            query,
            {"canonical_name": canonical_name, "alias": alias},
        )
        return len(result) > 0

    # ══════════════════════════════════════════════════════════════
    # Relationship CRUD / 关系 CRUD
    # ══════════════════════════════════════════════════════════════

    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict] = None,
    ) -> bool:
        """
        Create a relationship between two nodes (MERGE for idempotency).
        在两个节点之间创建关系（使用 MERGE 确保幂等）。

        Supports linking Document→Concept and Concept→Concept by matching
        on appropriate property (id for Document, name for Concept).

        Args:
            source_id:  Source node identifier / 源节点标识符
            target_id:  Target node identifier / 目标节点标识符
            rel_type:   Relationship type (e.g., "MENTIONS", "IS_A")
                       / 关系类型
            properties: Relationship properties (sanitized to primitives)
                       / 关系属性（自动清理）

        Returns:
            True if successful / 成功返回 True
        """
        sanitized_props = self._sanitize_properties(properties or {})

        query = f"""
        MATCH (a), (b)
        WHERE (a:Document AND a.id = $source_id)
           OR (a:Concept AND a.name = $source_id)
        AND (b:Document AND b.id = $target_id)
           OR (b:Concept AND b.name = $target_id)
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $properties,
            r.created_at = coalesce(r.created_at, datetime()),
            r.updated_at = datetime()
        RETURN r
        """
        result = self.execute_query(
            query,
            {
                "source_id": source_id,
                "target_id": target_id,
                "properties": sanitized_props,
            },
        )
        return len(result) > 0

    def link_concept_to_document(
        self,
        concept_name: str,
        doc_id: str,
        page: Optional[int] = None,
        offset: Optional[List[int]] = None,
        evidence: Optional[str] = None,
    ) -> bool:
        """
        Create a MENTIONS relationship between Document and Concept.
        创建 Document 和 Concept 之间的 MENTIONS 关系。

        Args:
            concept_name:  Concept name / 概念名称
            doc_id:        Document ID / 文档 ID
            page:          Page number where concept appears / 出现页码
            offset:        Text offset range [start, end] / 文本偏移范围
            evidence:      Contextual text evidence / 上下文文本证据

        Returns:
            True if successful / 成功返回 True
        """
        properties = {}
        if page is not None:
            properties["page"] = page
        if offset:
            properties["offset"] = offset
        if evidence:
            properties["evidence"] = evidence

        return self.create_relationship(
            doc_id, concept_name, "MENTIONS", properties
        )

    # ══════════════════════════════════════════════════════════════
    # Query Methods / 查询方法
    # ══════════════════════════════════════════════════════════════

    def get_all_nodes(
        self, label: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """
        Get all nodes, optionally filtered by label.
        获取所有节点，可选地按标签过滤。

        Args:
            label:  Node label filter (e.g., "Concept", "Document")
                   / 节点标签过滤
            limit:  Maximum nodes to return / 最大返回节点数

        Returns:
            List of node records / 节点记录列表
        """
        if label:
            query = f"MATCH (n:{label}) RETURN n LIMIT $limit"
        else:
            query = "MATCH (n) RETURN n LIMIT $limit"
        return self.execute_query(query, {"limit": limit})

    def get_all_relationships(
        self, rel_type: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """
        Get all relationships, optionally filtered by type.
        获取所有关系，可选地按类型过滤。

        Args:
            rel_type:  Relationship type filter / 关系类型过滤
            limit:     Maximum relationships to return / 最大返回关系数

        Returns:
            List of relationship records with source and target nodes
            包含源节点和目标节点的关系记录列表
        """
        if rel_type:
            query = (
                f"MATCH (a)-[r:{rel_type}]->(b) "
                f"RETURN a, r, b LIMIT $limit"
            )
        else:
            query = "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT $limit"
        return self.execute_query(query, {"limit": limit})

    def find_concept_by_name(self, name: str) -> Optional[Dict]:
        """
        Find a concept by exact name match.
        通过精确名称匹配查找概念。

        Args:
            name:  Concept name to find / 要查找的概念名称

        Returns:
            Record dict with 'c' key, or None if not found
        """
        query = "MATCH (c:Concept {name: $name}) RETURN c"
        result = self.execute_query(query, {"name": name})
        return result[0] if result else None

    def find_similar_concepts(
        self, name: str, threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find similar concepts with bilingual support.
        查找相似概念，支持中英文。

        Search strategies in priority order / 搜索策略优先级::

            1. Exact match (case-insensitive) / 精确匹配（不区分大小写）
            2. Substring containment / 子串包含
            3. Alias match / 别名匹配
            4. Fuzzy containment (both directions) / 双向模糊包含

        Args:
            name:       Concept name to search for / 要搜索的概念名称
            threshold:  Similarity threshold (reserved for future use)
                       / 相似度阈值（预留）

        Returns:
            List of matching concept records, ordered by relevance
            匹配的概念记录列表，按相关性排序
        """
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) = toLower($name)
           OR c.name CONTAINS $name
           OR $name CONTAINS c.name
           OR any(alias IN coalesce(c.aliases, [])
               WHERE toLower(alias) = toLower($name))
           OR any(alias IN coalesce(c.aliases, [])
               WHERE alias CONTAINS $name OR $name CONTAINS alias)
        RETURN c
        ORDER BY
            CASE
                WHEN toLower(c.name) = toLower($name) THEN 0
                WHEN c.name CONTAINS $name
                  OR $name CONTAINS c.name THEN 1
                ELSE 2
            END
        LIMIT 10
        """
        return self.execute_query(query, {"name": name})

    def search_concepts_by_alias(self, alias: str) -> List[Dict]:
        """
        Search concepts by alias.
        通过别名搜索概念。

        Args:
            alias:  The alias to search for / 要搜索的别名

        Returns:
            List of concepts that have this alias / 具有该别名的概念列表
        """
        query = """
        MATCH (c:Concept)
        WHERE toLower($alias)
              IN [toLower(a) | a IN coalesce(c.aliases, [])]
        RETURN c
        """
        return self.execute_query(query, {"alias": alias})

    # ══════════════════════════════════════════════════════════════
    # Topic Management / 主题管理
    # ══════════════════════════════════════════════════════════════

    def create_or_get_topic(self, topic_name: str) -> str:
        """
        Create or get a Topic root node (MERGE by name).
        创建或获取 Topic 根节点（按名称合并）。

        Topic nodes serve as root-level containers for organizing concepts
        into thematic groups. They are linked to documents via BELONGS_TO
        and to concepts via CONTAINS relationships.

        Args:
            topic_name:  Topic name / 主题名称

        Returns:
            Canonical topic name / 规范化的主题名称
        """
        query = """
        MERGE (t:Topic {name: $topic_name})
        ON CREATE SET
            t.created_at = datetime(),
            t.updated_at = datetime()
        ON MATCH SET
            t.updated_at = datetime()
        RETURN t.name as name
        """
        result = self.execute_query(query, {"topic_name": topic_name})
        return result[0]["name"] if result else topic_name

    def link_document_to_topic(self, doc_id: str, topic_name: str) -> bool:
        """
        Create BELONGS_TO relationship between Document and Topic.
        创建 Document 到 Topic 的 BELONGS_TO 关系。

        Args:
            doc_id:      Document ID / 文档 ID
            topic_name:  Topic name / 主题名称

        Returns:
            True if successful / 成功返回 True
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        MATCH (t:Topic {name: $topic_name})
        MERGE (d)-[r:BELONGS_TO]->(t)
        SET r.created_at = coalesce(r.created_at, datetime()),
            r.updated_at = datetime()
        RETURN r
        """
        result = self.execute_query(
            query, {"doc_id": doc_id, "topic_name": topic_name}
        )
        return len(result) > 0

    def link_concept_to_topic(
        self,
        concept_name: str,
        topic_name: str,
        page: Optional[int] = None,
        offset: Optional[List[int]] = None,
        evidence: Optional[str] = None,
        doc_id: Optional[str] = None,
    ) -> bool:
        """
        Create CONTAINS relationship between Topic and Concept.
        创建 Topic 到 Concept 的 CONTAINS 关系。

        Args:
            concept_name:  Concept name / 概念名称
            topic_name:    Topic name / 主题名称
            page:          Page number (optional) / 页码
            offset:        Text offset (optional) / 文本偏移
            evidence:      Evidence text (optional) / 证据文本
            doc_id:        Document ID (optional, for source tracking) / 文档 ID

        Returns:
            True if successful / 成功返回 True
        """
        properties = {}
        if page is not None:
            properties["page"] = page
        if offset:
            properties["offset"] = offset
        if evidence:
            properties["evidence"] = evidence
        if doc_id:
            properties["doc_id"] = doc_id

        query = """
        MATCH (t:Topic {name: $topic_name})
        MATCH (c:Concept {name: $concept_name})
        MERGE (t)-[r:CONTAINS]->(c)
        SET r += $properties,
            r.created_at = coalesce(r.created_at, datetime()),
            r.updated_at = datetime()
        RETURN r
        """
        result = self.execute_query(
            query,
            {
                "topic_name": topic_name,
                "concept_name": concept_name,
                "properties": properties,
            },
        )
        return len(result) > 0

    # ══════════════════════════════════════════════════════════════
    # Deletion Operations / 删除操作
    # ══════════════════════════════════════════════════════════════

    def delete_document(self, doc_id: str) -> dict:
        """
        Delete a Document node and all its relationships,
        then recursively delete orphan nodes.
        删除 Document 节点及其所有关系，然后递归删除孤立节点。

        The deletion cascade is::

            1. Count relationships for reporting
            2. DETACH DELETE the Document node (removes all its relationships)
            3. Recursively delete orphan nodes (nodes with zero edges remaining)
            4. Return deletion statistics

        Orphan nodes are deleted iteratively (up to 20 rounds) because
        deleting one orphan may create new orphans.

        Args:
            doc_id:  Document ID to delete / 要删除的文档 ID

        Returns:
            Dict with deletion stats:
                - edge_count: Number of edges the document had
                - orphan_nodes_deleted: Number of orphan nodes recursively deleted
        """
        # Count relationships for the document before deletion
        # 删除前统计文档的关系数
        info_query = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[r]-()
        RETURN count(DISTINCT r) as edge_count
        """
        info = self.execute_query(info_query, {"doc_id": doc_id})
        edge_count = info[0]["edge_count"] if info else 0

        # Delete the document and all its relationships / 删除文档及其所有关系
        delete_query = """
        MATCH (d:Document {id: $doc_id})
        DETACH DELETE d
        """
        self.execute_query(delete_query, {"doc_id": doc_id})

        # Recursively delete orphaned nodes / 递归删除孤立节点
        orphan_count = self._delete_orphan_nodes()

        return {
            "edge_count": edge_count,
            "orphan_nodes_deleted": orphan_count,
        }

    def _delete_orphan_nodes(self) -> int:
        """
        Recursively delete nodes that have no relationships.
        递归删除没有任何关系的孤立节点。

        Certain system/structural node types (Topic, RuntimeConfig) are
        excluded from orphan deletion because they serve as root containers
        that should persist even without edges.

        The deletion runs iteratively in rounds (up to 20 max) because
        removing one orphan may cause another node to become orphaned.

        Returns:
            Total number of orphan nodes deleted across all rounds
            所有轮次中删除的孤立节点总数
        """
        total_deleted = 0
        max_rounds = 20  # Safety limit to prevent infinite loops

        for _ in range(max_rounds):
            delete_query = """
            MATCH (n)
            WHERE NOT (n)--()
              AND NOT n:Topic
              AND NOT n:RuntimeConfig
            DETACH DELETE n
            RETURN count(n) as deleted_count
            """
            result = self.execute_query(delete_query)

            deleted_this_round = (
                result[0]["deleted_count"] if result else 0
            )
            if deleted_this_round == 0:
                break

            total_deleted += deleted_this_round

        return total_deleted


# Global singleton instance / 全局单例实例
neo4j_client = Neo4jClient()
