import pytest
from fastapi.testclient import TestClient


def test_create_page(client: TestClient):
    """测试创建 page"""
    payload = {
        "image_url": "http://localhost:9000/doc-edit/assets/ast_test123.png",
        "width": 1920,
        "height": 1080
    }
    response = client.post("/v1/pages", json=payload)

    assert response.status_code == 200
    data = response.json()

    # 验证响应字段
    assert "page_id" in data
    assert data["page_id"].startswith("page_")


def test_analyze_page_mock(client: TestClient):
    """测试使用 mock OCR 分析页面"""
    # 先创建 page
    create_payload = {
        "image_url": "http://localhost:9000/doc-edit/assets/ast_test123.png",
        "width": 1920,
        "height": 1080
    }
    create_response = client.post("/v1/pages", json=create_payload)
    assert create_response.status_code == 200
    page_id = create_response.json()["page_id"]

    # 调用 analyze
    analyze_payload = {
        "provider": "mock",
        "lang_hints": ["zh-Hans", "en"]
    }
    analyze_response = client.post(f"/v1/pages/{page_id}/analyze", json=analyze_payload)

    assert analyze_response.status_code == 200
    data = analyze_response.json()

    # 验证响应字段
    assert data["page_id"] == page_id
    assert data["width"] == 1920
    assert data["height"] == 1080
    assert "candidates" in data
    assert isinstance(data["candidates"], list)

    # 验证 mock 数据返回了候选框
    if len(data["candidates"]) > 0:
        candidate = data["candidates"][0]
        assert "id" in candidate
        assert "text" in candidate
        assert "confidence" in candidate
        assert "quad" in candidate
        assert "bbox" in candidate
        assert "angle_deg" in candidate


def test_get_candidates(client: TestClient):
    """测试获取候选框列表"""
    # 先创建 page
    create_payload = {
        "image_url": "http://localhost:9000/doc-edit/assets/ast_test123.png",
        "width": 1920,
        "height": 1080
    }
    create_response = client.post("/v1/pages", json=create_payload)
    assert create_response.status_code == 200
    page_id = create_response.json()["page_id"]

    # 先 analyze
    analyze_payload = {"provider": "mock"}
    client.post(f"/v1/pages/{page_id}/analyze", json=analyze_payload)

    # 获取候选框
    response = client.get(f"/v1/pages/{page_id}/candidates")

    assert response.status_code == 200
    data = response.json()

    assert data["page_id"] == page_id
    assert "candidates" in data


def test_analyze_page_not_found(client: TestClient):
    """测试分析不存在的 page"""
    analyze_payload = {"provider": "mock"}
    response = client.post("/v1/pages/page_notexist/analyze", json=analyze_payload)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_candidates_not_found(client: TestClient):
    """测试获取不存在的 page 的候选框"""
    response = client.get("/v1/pages/page_notexist/candidates")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
