"""
API 路由集成测试
测试所有 API 端点的基本功能
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.api
class TestUploadAPI:
    """文档上传 API 测试"""
    
    def test_list_documents(self):
        """测试获取文档列表"""
        response = client.get("/uploads")
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
    
    def test_upload_document(self, sample_document):
        """测试上传文档"""
        files = {"file": ("test.txt", sample_document, "text/plain")}
        response = client.post("/uploads", files=files)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert "filename" in data
    
    def test_get_document_detail(self):
        """测试获取文档详情"""
        # 先获取文档列表
        list_response = client.get("/uploads")
        documents = list_response.json()["documents"]
        
        if documents:
            doc_id = documents[0]["id"]
            response = client.get(f"/uploads/{doc_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == doc_id


@pytest.mark.api
class TestGraphAPI:
    """图谱查询 API 测试"""
    
    def test_visualize_graph(self):
        """测试图谱可视化"""
        response = client.get("/graph/visualize?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
    
    def test_get_graph_stats(self):
        """测试获取图谱统计"""
        response = client.get("/graph/stats")
        assert response.status_code == 200
        data = response.json()
        assert "node_count" in data or "total_nodes" in data
    
    def test_document_graph(self):
        """测试文档子图"""
        # 获取一个文档ID
        docs_response = client.get("/uploads")
        documents = docs_response.json()["documents"]
        
        if documents:
            doc_id = documents[0]["id"]
            response = client.get(f"/graph/documents/{doc_id}/graph?depth=2")
            assert response.status_code == 200
            data = response.json()
            assert "nodes" in data
            assert "edges" in data


@pytest.mark.api
class TestIngestAPI:
    """知识抽取 API 测试"""
    
    def test_start_ingestion(self):
        """测试启动知识抽取"""
        # 获取一个已上传的文档
        docs_response = client.get("/uploads")
        documents = docs_response.json()["documents"]
        
        if documents:
            doc_id = documents[0]["id"]
            response = client.post(f"/ingest/{doc_id}")
            assert response.status_code in [200, 202]
    
    def test_get_ingestion_status(self):
        """测试获取抽取状态"""
        response = client.get("/ingest/status")
        assert response.status_code == 200


@pytest.mark.api  
class TestQAAPI:
    """问答 API 测试"""
    
    def test_ask_question(self):
        """测试提问"""
        question_data = {
            "question": "什么是软件工程？",
            "context_limit": 5
        }
        response = client.post("/qa/ask", json=question_data)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data or "response" in data
    
    def test_get_qa_history(self):
        """测试获取问答历史"""
        response = client.get("/qa/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "history" in data


@pytest.mark.api
class TestKnowledgeCardAPI:
    """知识卡片 API 测试"""
    
    def test_list_concepts(self):
        """测试获取概念列表"""
        response = client.get("/knowledge-cards/concepts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))
    
    def test_get_concept_detail(self):
        """测试获取概念详情"""
        # 先获取概念列表
        list_response = client.get("/knowledge-cards/concepts")
        concepts = list_response.json()
        
        if isinstance(concepts, list) and concepts:
            concept_id = concepts[0].get("id") or concepts[0].get("name")
            if concept_id:
                response = client.get(f"/knowledge-cards/concepts/{concept_id}")
                assert response.status_code in [200, 404]


@pytest.mark.api
class TestSettingsAPI:
    """设置 API 测试"""
    
    def test_get_settings(self):
        """测试获取设置"""
        response = client.get("/settings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_update_settings(self):
        """测试更新设置"""
        settings_data = {
            "theme": "dark",
            "language": "zh"
        }
        response = client.put("/settings", json=settings_data)
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
