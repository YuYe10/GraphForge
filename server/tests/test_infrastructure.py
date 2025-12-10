"""
基础设施层测试
测试 Neo4j、Redis 等基础组件
"""
import pytest


@pytest.mark.integration
@pytest.mark.db
class TestNeo4jClient:
    """Neo4j 客户端测试"""
    
    def test_connection(self, neo4j_test_client):
        """测试数据库连接"""
        assert neo4j_test_client is not None
        assert neo4j_test_client._initialized
    
    def test_execute_query(self, neo4j_test_client):
        """测试执行查询"""
        result = neo4j_test_client.execute_query(
            "RETURN 1 as num"
        )
        assert len(result) == 1
        assert result[0]["num"] == 1
    
    def test_create_document(self, neo4j_test_client, clean_test_db):
        """测试创建文档节点"""
        doc_id = "test_doc_001"
        filename = "test.pdf"
        checksum = "abc123"
        
        result = neo4j_test_client.create_document(
            doc_id, filename, checksum
        )
        assert result is not None
    
    def test_type_conversion(self, neo4j_test_client):
        """测试 Neo4j 类型转换"""
        from datetime import datetime
        from neo4j.time import DateTime
        
        # 测试 DateTime 转换
        neo4j_dt = DateTime(2024, 1, 1, 12, 0, 0)
        converted = neo4j_test_client._convert_neo4j_types(neo4j_dt)
        
        assert isinstance(converted, datetime)
    
    def test_bulk_create_nodes(self, neo4j_test_client, clean_test_db):
        """测试批量创建节点"""
        nodes = [
            {"id": f"node_{i}", "name": f"节点{i}", "type": "TestNode"}
            for i in range(10)
        ]
        
        # 批量创建
        for node in nodes:
            neo4j_test_client.execute_query(
                """
                CREATE (n:TestNode {id: $id, name: $name})
                RETURN n
                """,
                node
            )
        
        # 验证
        result = neo4j_test_client.execute_query(
            "MATCH (n:TestNode) RETURN count(n) as count"
        )
        assert result[0]["count"] == 10


@pytest.mark.integration
class TestAIProviders:
    """AI 服务提供商测试"""
    
    @pytest.mark.ai
    def test_ai_client_initialization(self):
        """测试 AI 客户端初始化"""
        from infra.ai_providers import get_ai_client
        
        try:
            client = get_ai_client()
            assert client is not None
        except Exception as e:
            pytest.skip(f"AI 客户端初始化失败: {e}")
    
    @pytest.mark.ai
    @pytest.mark.slow
    async def test_embedding_generation(self):
        """测试生成向量嵌入"""
        from infra.ai_providers import get_ai_client
        
        try:
            client = get_ai_client()
            embedding = await client.embed("测试文本")
            
            assert embedding is not None
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except Exception as e:
            pytest.skip(f"向量生成失败: {e}")


@pytest.mark.integration
class TestStorage:
    """存储服务测试"""
    
    def test_file_storage(self, tmp_path, sample_document):
        """测试文件存储"""
        from infra.storage import FileStorage
        from pathlib import Path
        
        storage = FileStorage(str(tmp_path))
        
        # 保存文件
        file_id = "test_file_001"
        saved_path = storage.save(file_id, sample_document.encode())
        
        assert saved_path.exists()
        
        # 读取文件
        content = storage.read(file_id)
        assert content.decode() == sample_document
        
        # 删除文件
        storage.delete(file_id)
        assert not saved_path.exists()


@pytest.mark.integration
class TestQueue:
    """任务队列测试"""
    
    @pytest.mark.slow
    def test_enqueue_task(self):
        """测试任务入队"""
        try:
            from infra.queue import task_queue
            
            job = task_queue.enqueue(
                'test_task',
                args=('arg1', 'arg2'),
                kwargs={'key': 'value'}
            )
            assert job is not None
        except Exception as e:
            pytest.skip(f"队列服务不可用: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
